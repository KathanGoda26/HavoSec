"""Fail-closed tenant boundary for the new domain services.

Legacy routes retain their existing contracts until migrated explicitly.
No customer-supplied organization selector is accepted. Superadmin services must
explicitly opt into selecting a single organization; there is no implicit wildcard.
"""
from dataclasses import dataclass
from fastapi import HTTPException
from pymongo.errors import PyMongoError

from core.ids import canonical_id
from utils.roles import UserRole


@dataclass(frozen=True)
class OrganizationScope:
    organization_id: str

    def query(self, **filters):
        if 'organization_id' in filters:
            raise ValueError('Organization scope cannot be overridden')
        return {**filters, 'organization_id': self.organization_id}


async def resolve_organization(user, repository, *, platform_organization_id=None):
    role = user.get('role')
    if role == UserRole.SUPERADMIN.value:
        if platform_organization_id is None:
            raise HTTPException(403, 'Select an organization through an authorized platform operation')
        selected = platform_organization_id
    elif role in {UserRole.ADMIN.value, UserRole.USER.value}:
        if platform_organization_id is not None:
            raise HTTPException(403, 'Organization selection is not permitted')
        selected = user.get('organizationId')
        if not selected:
            raise HTTPException(403, 'Account must be assigned to an organization')
    else:
        raise HTTPException(403, 'Insufficient permissions')

    try:
        organization_id = canonical_id(selected)
    except HTTPException as exc:
        raise HTTPException(403, 'Organization assignment is invalid') from exc
    try:
        organization = await repository.find_by_id(organization_id)
    except PyMongoError as exc:
        # Do not disclose server topology, credentials or database error details.
        raise HTTPException(503, 'Organization database is unavailable') from exc
    if not organization:
        raise HTTPException(403, 'Organization assignment is unavailable')
    if organization.get('status', 'active') != 'active' or organization.get('isActive', True) is False:
        raise HTTPException(403, 'Organization is inactive')
    return OrganizationScope(organization_id)
