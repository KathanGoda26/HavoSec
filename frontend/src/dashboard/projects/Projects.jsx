import React from 'react'
import { Link, NavLink, Outlet, useParams } from 'react-router-dom'
import Card from '@/components/ui/Card'
import ResourceState from '@/components/ui/ResourceState'
import usePollingResource from '@/hooks/usePollingResource'
import { securityApi, displayDate } from '@/services/securityApi'

export default function Projects() {
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.listProjects({ limit: 100 }), [])
  const projects = data?.items || []
  return (
    <div className="projects-page">
      <h1 className="page-title">Projects</h1>
      <p className="page-subtitle">Organization-scoped applications and repositories managed by HavoSec.</p>
      <ResourceState loading={loading} error={error} onRetry={reload} noun="projects" />
      {!loading && !error && (projects.length ? <div className="projects-grid">
        {projects.map(project => (
          <Card key={project.id} title={project.name} footer={<Link className="btn-primary" to={`/dashboard/projects/${project.id}/overview`}>Open Project</Link>}>
            <p>{project.description || 'No project description provided.'}</p>
            <span className="status-badge">{project.status}</span>
            <p>Created {displayDate(project.created_at)}</p>
          </Card>
        ))}
      </div> : <div className="empty-state"><h2>No Projects</h2><p>No projects are available in this workspace.</p></div>)}
    </div>
  )
}

export function ProjectLayout() {
  const { projectId } = useParams()
  const { data: project, loading, error, reload } = usePollingResource(
    () => securityApi.getProject(projectId), [projectId])
  if (loading || error) return <ResourceState loading={loading} error={error} onRetry={reload} noun="project" />
  return (
    <div className="projects-page">
      <Link to="/dashboard/projects">← Projects</Link>
      <h1 className="page-title">{project.name}</h1>
      <p className="page-subtitle">{project.description || 'No project description provided.'} · {project.status}</p>
      <nav className="project-tabs" aria-label="Project sections">
        {['overview', 'assets', 'findings', 'remediation', 'activity'].map(section => <NavLink key={section} className={({ isActive }) => `filter-btn ${isActive ? 'active' : ''}`} to={`/dashboard/projects/${projectId}/${section}`}>{section.charAt(0).toUpperCase() + section.slice(1)}</NavLink>)}
        <NavLink className={({ isActive }) => `filter-btn ${isActive ? 'active' : ''}`} to={`/dashboard/projects/${projectId}/security-runs`}>Security Runs</NavLink>
      </nav>
      <Outlet key={projectId} />
    </div>
  )
}

export function ProjectOverview() {
  const { projectId } = useParams()
  const { data, loading, error, reload } = usePollingResource(
    () => securityApi.getOverview({ project_id: projectId }), [projectId])
  if (loading || error) return <ResourceState loading={loading} error={error} onRetry={reload} noun="project summary" />
  const latest = data.latest_security_run
  const sections = [
    ['Assets', data.counts.assets, 'assets', 'organization-scoped assets'],
    ['Security Runs', data.counts.security_runs, 'security-runs', latest ? `Latest: ${latest.status}` : 'No completed or queued runs'],
    ['Findings', data.open_findings, 'findings', `${data.critical_findings} critical open`],
    ['Remediation', data.counts.remediations, 'remediation', 'remediation records'],
    ['Activity', data.recent_activity.length, 'activity', 'most recent recorded events'],
  ]
  return <div className="projects-grid">{sections.map(([title, count, path, detail]) => <Card key={path} title={title} footer={<Link to={`../${path}`} className="btn-secondary">View {title}</Link>}><p>{count} {detail}</p></Card>)}</div>
}
