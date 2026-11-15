import asyncio
from datetime import datetime, timezone

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from integrations.github.client import GitHubAppClient
from integrations.github.config import GitHubAppSettings


def make_private_key(path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path.write_bytes(private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))


def test_installation_token_is_ephemeral_and_repository_response_is_minimal(tmp_path):
    key_path = tmp_path / "app.pem"
    make_private_key(key_path)
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/access_tokens"):
            return httpx.Response(201, json={
                "token": "temporary-secret-token",
                "expires_at": "2026-09-04T13:00:00Z",
            })
        return httpx.Response(200, json={"repositories": [{
            "id": 1357212288,
            "full_name": "KathanGoda26/havosec-github-integration-test",
            "private": True,
            "default_branch": "main",
            "untrusted_extra": "discarded",
        }]})

    settings = GitHubAppSettings(4830110, key_path, 159047858)
    client = GitHubAppClient(settings, httpx.MockTransport(handler))
    repositories = asyncio.run(client.list_installation_repositories())

    assert repositories == [{
        "id": 1357212288,
        "full_name": "KathanGoda26/havosec-github-integration-test",
        "private": True,
        "default_branch": "main",
    }]
    assert requests[0].method == "POST"
    assert requests[1].headers["authorization"] == "Bearer temporary-secret-token"
    assert "temporary-secret-token" not in repr(client)


def test_token_repr_redacts_secret(tmp_path):
    key_path = tmp_path / "app.pem"
    make_private_key(key_path)

    def handler(request):
        return httpx.Response(201, json={
            "token": "must-not-leak",
            "expires_at": datetime.now(timezone.utc).isoformat(),
        })

    client = GitHubAppClient(
        GitHubAppSettings(4830110, key_path, 159047858),
        httpx.MockTransport(handler),
    )
    token = asyncio.run(client.create_installation_token())
    assert "must-not-leak" not in repr(token)
