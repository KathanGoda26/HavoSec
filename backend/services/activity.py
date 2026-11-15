from core.domain_api import document_view


class ActivityService:
    def __init__(self, repository, projects):
        self.repository = repository
        self.projects = projects

    async def list(self, scope, limit, offset, project_id=None):
        if project_id is not None:
            project = await self.projects.get_document(scope, project_id)
            project_id = str(project['_id'])
        items, total = await self.repository.list(scope, limit, offset, project_id)
        return {'items': [document_view(item) for item in items], 'total': total, 'limit': limit, 'offset': offset}
