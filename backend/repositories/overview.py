import asyncio
from models.findings import Severity, FindingStatus


class OverviewRepository:
    def __init__(self, db):
        self.db = db

    async def counts(self, scope, project_id=None):
        filters = {'project_id': project_id} if project_id else {}
        names = ['projects', 'assets', 'security_runs', 'findings', 'remediations']
        queries = []
        for name in names:
            if name == 'projects' and project_id:
                from core.ids import object_id
                query = scope.query(_id=object_id(project_id))
            else:
                query = scope.query(**filters)
            queries.append(self.db[name].count_documents(query))
        counts = dict(zip(names, await asyncio.gather(*queries)))
        # Explicit enum states exclude malformed external records from open counts.
        open_states = [s.value for s in FindingStatus if s != FindingStatus.RESOLVED]
        open_counts = await asyncio.gather(*[
            self.db.findings.count_documents(scope.query(**filters, status=status)) for status in open_states])
        critical_counts = await asyncio.gather(*[
            self.db.findings.count_documents(scope.query(**filters, status=status, severity='critical')) for status in open_states])
        severity = dict(zip([s.value for s in Severity], await asyncio.gather(*[
            self.db.findings.count_documents(scope.query(**filters, severity=s.value)) for s in Severity])))
        return {'counts': counts, 'open_findings': sum(open_counts),
                'critical_findings': sum(critical_counts), 'severity_counts': severity}
