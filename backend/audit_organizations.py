"""Read-only migration preflight. No --apply mode, inferred mappings or writes.

Run: backend/venv/Scripts/python.exe backend/audit_organizations.py
Output contains IDs and issue classifications, never credentials or account email.
"""
import asyncio
import json
from bson import ObjectId
from core.database import load_backend_environment, DatabaseSettings, create_database_client
from core.membership import MEMBERSHIP_FIELDS, membership_value
from utils.roles import normalize_role


def audit_memberships(accounts, organizations):
    by_id = {str(org['_id']): org for org in organizations}
    issues = []
    valid = 0
    for account in accounts:
        if normalize_role(account.get('role')) == 'superadmin':
            continue
        identity, state = membership_value(account)
        if state == 'assigned':
            if not ObjectId.is_valid(identity):
                state = 'invalid'
            elif identity not in by_id:
                state = 'dangling'
            else:
                org = by_id[identity]
                if org.get('isActive', True) is False or org.get('status', 'active') != 'active':
                    state = 'inactive'
                else:
                    valid += 1
                    continue
        issues.append({'user_id': str(account['_id']), 'issue': state, 'organization_id': identity})
    return {'mode': 'read_only', 'valid_customer_assignments': valid, 'issues': issues,
            'organizations_missing_metadata': [str(org['_id']) for org in organizations
                if any(key not in org for key in ('slug', 'status', 'created_at', 'updated_at'))]}


async def main():
    load_backend_environment()
    settings = DatabaseSettings.from_environment()
    client = create_database_client(settings)
    try:
        db = client[settings.database_name]
        accounts = [row async for row in db.users.find({}, {'role': 1, **{key: 1 for key in MEMBERSHIP_FIELDS}})]
        organizations = [row async for row in db.client_companies.find({},
            {'status': 1, 'isActive': 1, 'slug': 1, 'created_at': 1, 'updated_at': 1})]
        print(json.dumps(audit_memberships(accounts, organizations), indent=2))
    finally:
        client.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception:
        raise SystemExit('Organization audit failed; verify database configuration and availability.')
