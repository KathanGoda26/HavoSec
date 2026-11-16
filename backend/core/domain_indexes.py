"""Explicit domain indexes; never installed during API startup."""
from pymongo import IndexModel


def domain_index_specs():
    specs = {}
    for collection in ['projects', 'assets', 'security_runs', 'missions', 'findings', 'remediations', 'activity_events']:
        indexes = [IndexModel([('organization_id', 1), ('created_at', -1), ('_id', -1)], name='org_recent')]
        if collection != 'projects':
            indexes.append(IndexModel([('organization_id', 1), ('project_id', 1), ('created_at', -1), ('_id', -1)], name='org_project_recent'))
        if collection != 'activity_events':
            indexes.append(IndexModel([('organization_id', 1), ('status', 1), ('created_at', -1), ('_id', -1)], name='org_status_recent'))
        specs[collection] = indexes
    specs['missions'].append(IndexModel([('organization_id', 1), ('request_key', 1)],
                                       name='org_request_key', unique=True))
    specs['missions'].append(IndexModel([('organization_id', 1)], name='org_mission_slot',
                                       unique=True, partialFilterExpression={'orchestration.slot': True}))
    specs['mission_outbox'] = [
        IndexModel([('status', 1), ('created_at', 1), ('_id', 1)], name='pending_commands'),
        IndexModel([('status', 1), ('available_at', 1), ('created_at', 1), ('_id', 1)], name='dispatch_schedule'),
    ]
    specs['mission_execution_events'] = [
        IndexModel([('organization_id', 1), ('mission_id', 1), ('created_at', -1), ('_id', -1)],
                   name='org_mission_execution_history'),
    ]
    specs['findings'].extend([
        IndexModel([('organization_id', 1), ('severity', 1), ('status', 1)], name='org_severity_status'),
        IndexModel([('organization_id', 1), ('asset_id', 1)], name='org_asset'),
        IndexModel([('organization_id', 1), ('security_run_id', 1)], name='org_run'),
        IndexModel([('organization_id', 1), ('fingerprint', 1)], name='org_fingerprint', unique=True,
                   partialFilterExpression={'fingerprint': {'$type': 'string'}}),
    ])
    specs['remediations'].append(IndexModel([('organization_id', 1), ('finding_id', 1)], name='org_finding'))
    specs['scanner_results'] = [
        IndexModel([('organization_id', 1), ('security_run_id', 1), ('scanner', 1)],
                   name='org_run_scanner', unique=True),
        IndexModel([('created_at', 1)], name='created_ttl', expireAfterSeconds=2592000),
    ]
    specs['github_integrations'] = [
        IndexModel([('organization_id', 1)], name='organization_unique', unique=True),
        IndexModel([('installation_id', 1)], name='installation_unique', unique=True),
        IndexModel([('status', 1), ('updated_at', -1)], name='status_updated'),
    ]
    specs['github_repositories'] = [
        IndexModel([('organization_id', 1), ('repository_id', 1)], name='org_repository_unique', unique=True),
        IndexModel([('integration_id', 1), ('repository_id', 1)], name='integration_repository_unique', unique=True),
        IndexModel([('organization_id', 1), ('authorized', 1), ('full_name', 1)], name='org_authorized_name'),
    ]
    specs['assets'].append(IndexModel(
        [('organization_id', 1), ('source_control.repository_id', 1)],
        name='org_github_repository',
        partialFilterExpression={'source_control.provider': 'github'},
    ))
    specs['github_connection_states'] = [
        IndexModel([('expires_at', 1)], name='expires_ttl', expireAfterSeconds=0),
    ]
    specs['pull_requests'] = [
        IndexModel([('organization_id', 1), ('remediation_id', 1)],
                   name='one_pr_per_remediation', unique=True),
        IndexModel([('organization_id', 1), ('status', 1), ('updated_at', -1)],
                   name='org_status_updated'),
    ]
    specs['github_webhook_deliveries'] = [
        IndexModel([('expires_at', 1)], name='delivery_ttl', expireAfterSeconds=0),
    ]
    return specs


async def ensure_domain_indexes(db):
    return {name: await db[name].create_indexes(indexes) for name, indexes in domain_index_specs().items()}
