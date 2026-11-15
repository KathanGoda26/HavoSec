import asyncio


class OverviewService:
    def __init__(self, repository, projects, findings, runs, activity):
        self.repository, self.projects = repository, projects
        self.findings, self.runs, self.activity = findings, runs, activity

    async def get(self, scope, project_id=None):
        if project_id is not None:
            project = await self.projects.get_document(scope, project_id)
            project_id = str(project['_id'])
        counts, findings, runs, activity = await asyncio.gather(
            self.repository.counts(scope, project_id),
            self.findings.list_filtered(scope, 5, 0, project_id=project_id),
            self.runs.list(scope, 5, 0, project_id=project_id),
            self.activity.list(scope, 5, 0, project_id=project_id))
        return {**counts, 'security_score': None, 'security_score_status': 'unavailable',
                'latest_security_run': runs['items'][0] if runs['items'] else None,
                'recent_findings': findings['items'], 'recent_runs': runs['items'],
                'recent_activity': activity['items']}
