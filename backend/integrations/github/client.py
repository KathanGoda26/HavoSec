"""Minimal GitHub App API client with ephemeral installation tokens."""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote
import base64

import httpx

from .app_auth import create_app_jwt
from .config import GitHubAppSettings, GitHubConfigurationError


class GitHubAPIError(RuntimeError):
    """Safe integration error that excludes credentials and response bodies."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class InstallationToken:
    value: str
    expires_at: datetime

    def __repr__(self):
        return f"InstallationToken(value=<redacted>, expires_at={self.expires_at!r})"


class GitHubAppClient:
    def __init__(self, settings: GitHubAppSettings, transport: httpx.AsyncBaseTransport | None = None):
        if settings.installation_id is None:
            raise GitHubConfigurationError("GITHUB_INSTALLATION_ID is required")
        self.settings = settings
        self.transport = transport

    async def create_installation_token(self) -> InstallationToken:
        payload = await self._request(
            "POST",
            f"/app/installations/{self.settings.installation_id}/access_tokens",
            bearer=create_app_jwt(self.settings),
        )
        token = payload.get("token")
        expires_at = payload.get("expires_at")
        if not isinstance(token, str) or not token or not isinstance(expires_at, str):
            raise GitHubAPIError("GitHub returned an invalid installation token response")
        try:
            parsed_expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned an invalid installation token expiry") from exc
        return InstallationToken(token, parsed_expiry)

    async def get_installation(self) -> dict:
        payload = await self._request(
            "GET",
            f"/app/installations/{self.settings.installation_id}",
            bearer=create_app_jwt(self.settings),
        )
        account = payload.get("account") or {}
        if payload.get("id") != self.settings.installation_id or not isinstance(account, dict):
            raise GitHubAPIError("GitHub returned an invalid installation response")
        return {
            "installation_id": payload["id"],
            "account_id": account.get("id"),
            "account_login": account.get("login"),
            "account_type": account.get("type"),
            "permissions": payload.get("permissions") or {},
            "repository_selection": payload.get("repository_selection") or "selected",
        }

    async def list_installation_repositories(self) -> list[dict]:
        token = await self.create_installation_token()
        payload = await self._request("GET", "/installation/repositories", bearer=token.value)
        repositories = payload.get("repositories")
        if not isinstance(repositories, list):
            raise GitHubAPIError("GitHub returned an invalid repository response")
        return [
            {
                "id": repository["id"],
                "full_name": repository["full_name"],
                "private": bool(repository.get("private")),
                "default_branch": repository.get("default_branch"),
            }
            for repository in repositories
            if isinstance(repository, dict)
            and isinstance(repository.get("id"), int)
            and isinstance(repository.get("full_name"), str)
        ]

    async def get_branch_head(self, repository: str, branch: str) -> str:
        token = await self.create_installation_token()
        payload = await self._request(
            "GET", f"/repos/{_repository_path(repository)}/git/ref/heads/{quote(branch, safe='')}",
            bearer=token.value,
        )
        sha = ((payload.get("object") or {}).get("sha"))
        if not isinstance(sha, str) or len(sha) != 40:
            raise GitHubAPIError("GitHub returned an invalid branch response")
        return sha

    async def get_commit(self, repository: str, commit_sha: str) -> dict:
        token = await self.create_installation_token()
        return await self._request(
            "GET", f"/repos/{_repository_path(repository)}/git/commits/{commit_sha}",
            bearer=token.value,
        )

    async def get_tree(self, repository: str, tree_sha: str) -> dict[str, dict]:
        token = await self.create_installation_token()
        payload = await self._request(
            "GET", f"/repos/{_repository_path(repository)}/git/trees/{tree_sha}?recursive=1",
            bearer=token.value,
        )
        if payload.get("truncated") is True:
            raise GitHubAPIError("GitHub repository tree is too large for safe patch delivery")
        entries = payload.get("tree")
        if not isinstance(entries, list):
            raise GitHubAPIError("GitHub returned an invalid tree response")
        return {entry["path"]: entry for entry in entries
                if isinstance(entry, dict) and isinstance(entry.get("path"), str)}

    async def get_blob(self, repository: str, blob_sha: str, *, max_bytes: int = 10_000_000) -> bytes:
        token = await self.create_installation_token()
        payload = await self._request(
            "GET", f"/repos/{_repository_path(repository)}/git/blobs/{blob_sha}",
            bearer=token.value,
        )
        if payload.get("encoding") != "base64" or not isinstance(payload.get("content"), str):
            raise GitHubAPIError("GitHub returned an invalid blob response")
        if not isinstance(payload.get("size"), int) or payload["size"] > max_bytes:
            raise GitHubAPIError("GitHub source file exceeds the safe size limit")
        try:
            encoded = "".join(payload["content"].split())
            content = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned an invalid blob response") from exc
        if len(content) != payload["size"] or len(content) > max_bytes:
            raise GitHubAPIError("GitHub returned an invalid blob size")
        return content

    async def create_blob(self, repository: str, content_base64: str) -> str:
        payload = await self._installation_request(
            "POST", f"/repos/{_repository_path(repository)}/git/blobs",
            json={"content": content_base64, "encoding": "base64"},
        )
        return _sha(payload, "blob")

    async def create_tree(self, repository: str, base_tree: str, entries: list[dict]) -> str:
        payload = await self._installation_request(
            "POST", f"/repos/{_repository_path(repository)}/git/trees",
            json={"base_tree": base_tree, "tree": entries},
        )
        return _sha(payload, "tree")

    async def create_commit(self, repository: str, message: str, tree: str, parent: str,
                            timestamp: str) -> str:
        payload = await self._installation_request(
            "POST", f"/repos/{_repository_path(repository)}/git/commits",
            json={"message": message, "tree": tree, "parents": [parent],
                  "author": {"name": "HavoSec", "email": "remediation@havosec.com", "date": timestamp},
                  "committer": {"name": "HavoSec", "email": "remediation@havosec.com", "date": timestamp}},
        )
        return _sha(payload, "commit")

    async def create_branch(self, repository: str, branch: str, commit_sha: str) -> None:
        await self._installation_request(
            "POST", f"/repos/{_repository_path(repository)}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
        )

    async def create_pull_request(self, repository: str, title: str, body: str,
                                  branch: str, base_branch: str) -> dict:
        payload = await self._installation_request(
            "POST", f"/repos/{_repository_path(repository)}/pulls",
            json={"title": title, "body": body, "head": branch, "base": base_branch},
        )
        if not isinstance(payload.get("number"), int) or not isinstance(payload.get("html_url"), str):
            raise GitHubAPIError("GitHub returned an invalid pull request response")
        return {"number": payload["number"], "url": payload["html_url"],
                "state": payload.get("state", "open")}

    async def find_pull_request(self, repository: str, owner: str, branch: str,
                                base_branch: str) -> dict | None:
        token = await self.create_installation_token()
        path = (f"/repos/{_repository_path(repository)}/pulls?state=all&head="
                f"{quote(owner + ':' + branch, safe='')}&base={quote(base_branch, safe='')}")
        payload = await self._request_list("GET", path, bearer=token.value)
        for item in payload:
            if isinstance(item, dict) and isinstance(item.get("number"), int):
                return {"number": item["number"], "url": item.get("html_url"),
                        "state": item.get("state", "open")}
        return None

    async def _installation_request(self, method: str, path: str, *, json: dict):
        token = await self.create_installation_token()
        return await self._request(method, path, bearer=token.value, json=json)

    async def _request(self, method: str, path: str, *, bearer: str, json: dict | None = None) -> dict:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {bearer}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "HavoSec-GitHub-Integration",
        }
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.api_url,
                headers=headers,
                timeout=15.0,
                transport=self.transport,
            ) as client:
                response = await client.request(method, path, json=json)
                if response.is_error:
                    raise GitHubAPIError("GitHub integration request failed", response.status_code)
                payload = response.json()
        except GitHubAPIError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise GitHubAPIError("GitHub integration request failed") from exc
        if not isinstance(payload, dict):
            raise GitHubAPIError("GitHub returned an invalid response")
        return payload

    async def _request_list(self, method: str, path: str, *, bearer: str) -> list:
        headers = {
            "Accept": "application/vnd.github+json", "Authorization": f"Bearer {bearer}",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "HavoSec-GitHub-Integration",
        }
        try:
            async with httpx.AsyncClient(base_url=self.settings.api_url, headers=headers,
                                         timeout=15.0, transport=self.transport) as client:
                response = await client.request(method, path)
                if response.is_error:
                    raise GitHubAPIError("GitHub integration request failed", response.status_code)
                payload = response.json()
        except GitHubAPIError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise GitHubAPIError("GitHub integration request failed") from exc
        if not isinstance(payload, list):
            raise GitHubAPIError("GitHub returned an invalid response")
        return payload


def _repository_path(repository: str) -> str:
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise GitHubAPIError("GitHub repository identifier is invalid")
    owner, name = repository.split("/", 1)
    if not owner or not name or any(character.isspace() for character in repository):
        raise GitHubAPIError("GitHub repository identifier is invalid")
    return f"{quote(owner, safe='')}/{quote(name, safe='')}"


def _sha(payload: dict, kind: str) -> str:
    sha = payload.get("sha")
    if not isinstance(sha, str) or len(sha) != 40:
        raise GitHubAPIError(f"GitHub returned an invalid {kind} response")
    return sha
