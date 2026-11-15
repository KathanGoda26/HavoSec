from fastapi import HTTPException

from integrations.github.webhooks import aggregate_checks, check_state


class GitHubWebhookService:
    def __init__(self, repository):
        self.repository = repository

    async def process(self, delivery_id, event_type, payload):
        installation_id = _positive_id((payload.get('installation') or {}).get('id'))
        repository_id = _positive_id((payload.get('repository') or {}).get('id'))
        if not installation_id or not repository_id:
            raise HTTPException(400, 'GitHub webhook identity is invalid')
        if event_type == 'pull_request':
            return await self._pull_request(delivery_id, payload, installation_id, repository_id)
        return await self._checks(delivery_id, event_type, payload, installation_id, repository_id)

    async def _pull_request(self, delivery_id, payload, installation_id, repository_id):
        pull = payload.get('pull_request') or {}
        number = _positive_id(payload.get('number') or pull.get('number'))
        if not number:
            raise HTTPException(400, 'GitHub pull request identity is invalid')
        action = payload.get('action')

        def transform(record):
            status = record.get('status')
            extra = {}
            if action in {'opened', 'reopened', 'synchronize'}:
                status = 'open'
            elif action == 'closed':
                status = 'merged' if pull.get('merged') is True else 'closed'
            else:
                return {}, {}
            head_sha = ((pull.get('head') or {}).get('sha'))
            if action == 'synchronize' and head_sha != record.get('commit_sha'):
                extra = {'reverification_status': 'failed', 'checks_status': 'unknown',
                         'error': 'Pull request branch changed outside the verified HavoSec operation'}
            readiness = ('ready_for_review' if status == 'open' and
                         record.get('checks_status') == 'passing' and
                         record.get('reverification_status') == 'verified' and not extra
                         else 'waiting')
            extra['readiness_status'] = readiness
            if status == record.get('status') and not extra:
                return {}, {}
            return {'status': status, **extra}, {
                'event_type': 'pull_request_status_updated',
                'message': 'Pull request status updated',
                'pr_number': number, 'status': status,
            }

        duplicate, record = await self.repository.apply_webhook_once(
            delivery_id, 'pull_request',
            {'installation_id': installation_id, 'repository_id': repository_id, 'pr_number': number},
            transform,
        )
        return {'accepted': True, 'duplicate': duplicate, 'matched': record is not None}

    async def _checks(self, delivery_id, event_type, payload, installation_id, repository_id):
        item = payload.get(event_type) or {}
        check_id = _positive_id(item.get('id'))
        head_sha = item.get('head_sha')
        if not check_id or not isinstance(head_sha, str) or len(head_sha) != 40:
            raise HTTPException(400, 'GitHub check identity is invalid')
        state = check_state(item.get('status'), item.get('conclusion'))
        key = f'{event_type}:{check_id}'

        def transform(record):
            checks = dict(record.get('checks') or {})
            checks[key] = state
            aggregate = aggregate_checks(checks)
            if checks == record.get('checks') and aggregate == record.get('checks_status'):
                return {}, {}
            readiness = ('ready_for_review' if aggregate == 'passing' and
                         record.get('reverification_status') == 'verified' and
                         record.get('status') == 'open' else 'waiting')
            return {'checks': checks, 'checks_status': aggregate,
                    'readiness_status': readiness}, {
                'event_type': 'pull_request_checks_updated',
                'message': 'Pull request checks updated',
                'checks_status': aggregate, 'check_type': event_type,
            }

        duplicate, record = await self.repository.apply_webhook_once(
            delivery_id, event_type,
            {'installation_id': installation_id, 'repository_id': repository_id, 'commit_sha': head_sha},
            transform,
        )
        return {'accepted': True, 'duplicate': duplicate, 'matched': record is not None}


def _positive_id(value):
    return value if isinstance(value, int) and value > 0 else None
