import asyncio
import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from routes.client_dashboard import get_system_health
from utils.auth import require_roles
from utils.roles import UserRole


@pytest.mark.parametrize('role', [UserRole.ADMIN.value, UserRole.USER.value])
def test_platform_role_dependency_denies_customer(role):
    guard = require_roles(UserRole.SUPERADMIN)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(guard(user={'role': role}))
    assert exc.value.status_code == 403


def test_platform_health_endpoint_has_superadmin_guard():
    # Exercise the actual dependency attached to the endpoint, not a UI filter.
    import inspect
    guard = inspect.signature(get_system_health).parameters['user'].default.dependency
    with pytest.raises(HTTPException) as exc:
        asyncio.run(guard(user={'role': UserRole.ADMIN.value}))
    assert exc.value.status_code == 403
    user = asyncio.run(guard(user={'role': UserRole.SUPERADMIN.value}))
    request = Request({'type': 'http', 'app': FastAPI()})
    assert 'systemHealth' in asyncio.run(get_system_health(request, user))
