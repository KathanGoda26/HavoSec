from datetime import datetime, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from integrations.github.app_auth import create_app_jwt
from integrations.github.config import GitHubAppSettings, GitHubConfigurationError


def make_private_key(path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path.write_bytes(private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    return private_key.public_key()


def test_settings_load_key_by_path_without_exposing_it(monkeypatch, tmp_path):
    key_path = tmp_path / "app.pem"
    make_private_key(key_path)
    monkeypatch.setenv("GITHUB_APP_ID", "4830110")
    monkeypatch.setenv("GITHUB_INSTALLATION_ID", "159047858")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", str(key_path))

    settings = GitHubAppSettings.from_environment(require_installation=True)

    assert settings.installation_id == 159047858
    assert str(key_path) not in repr(settings)
    assert "PRIVATE KEY" not in repr(settings)


def test_configuration_fails_closed_for_missing_key(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_APP_ID", "4830110")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY_PATH", str(tmp_path / "missing.pem"))
    with pytest.raises(GitHubConfigurationError, match="unavailable"):
        GitHubAppSettings.from_environment()


def test_app_jwt_is_rs256_signed_and_short_lived(tmp_path):
    key_path = tmp_path / "app.pem"
    public_key = make_private_key(key_path)
    settings = GitHubAppSettings(4830110, key_path, 159047858)
    now = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)

    token = create_app_jwt(settings, now=now)
    claims = jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_exp": False})

    assert claims["iss"] == "4830110"
    assert claims["exp"] - claims["iat"] == 600
