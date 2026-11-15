"""Disposable, database-backed acceptance proof for the single-agent remediation loop.

The command is intentionally fixed to HavoSec's checked-in vulnerable fixture. It
requires a real superadmin login and never prints the password, token, or database
connection string. Run with --run; credentials may be supplied interactively or
through HAVOSEC_ACCEPTANCE_EMAIL and HAVOSEC_ACCEPTANCE_PASSWORD.
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import httpx
from bson import ObjectId
from fastapi import FastAPI

from core.database import DatabaseSettings, create_database_client, load_backend_environment

load_backend_environment()

from models.remediations import RemediationProposal
from routes.activity import router as activity_router
from routes.admin_auth import router as admin_auth_router
from routes.assets import router as assets_router
from routes.clients import router as clients_router
from routes.findings import router as findings_router
from routes.projects import router as projects_router
from routes.remediations import router as remediations_router
from routes.security_runs import router as runs_router
from security_engine.pipeline import SecurityPipeline
from security_engine.remediation_pipeline import RemediationPipeline
from security_engine.remediation_workspace import PatchApplicator, RemediationWorkspace
from security_engine.repository import GitRepository
from security_engine.scanners.semgrep import SemgrepScanner
from security_engine.storage import WorkerRepository
from security_engine.workspace import RunWorkspace


FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "vulnerable-repository"
PATCH = FIXTURE / "known-good-eval-fix.diff"
SCANNER_BIN = Path(__file__).parent / ".tools" / "semgrep-venv" / "Scripts"
FIXED_REPOSITORY = "https://github.com/havosec/single-agent-runtime-fixture"
TARGET_RULE_SUFFIX = "havosec.python.eval"
PROJECT_CHILD_COLLECTIONS = (
    "activity_events", "scanner_results", "remediations", "findings",
    "security_runs", "assets",
)


def acceptance_app(db):
    app = FastAPI()
    app.state.db = db
    app.include_router(admin_auth_router, prefix="/api/admin/auth")
    app.include_router(clients_router, prefix="/api/admin/clients")
    for router, prefix in (
        (projects_router, "/api/projects"), (assets_router, "/api/assets"),
        (runs_router, "/api/security-runs"), (findings_router, "/api/findings"),
        (remediations_router, "/api/remediations"), (activity_router, "/api/activity"),
    ):
        app.include_router(router, prefix=prefix)
    return app


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def git_state(root: Path) -> tuple[str, bool]:
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip().lower()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root,
        check=True, capture_output=True, text=True,
    ).stdout
    return head, not bool(status.strip())


def create_fixture_repository(parent: Path) -> tuple[Path, str]:
    source = parent / "source"
    source.mkdir()
    shutil.copy2(FIXTURE / "app.py", source / "app.py")
    commands = (
        ["git", "init", "--quiet"],
        ["git", "config", "user.name", "HavoSec Acceptance"],
        ["git", "config", "user.email", "acceptance@invalid.local"],
        ["git", "add", "--", "app.py"],
        ["git", "commit", "--quiet", "-m", "immutable acceptance fixture"],
    )
    for command in commands:
        subprocess.run(command, cwd=source, check=True, capture_output=True)
    commit = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=source, check=True,
        capture_output=True, text=True,
    ).stdout.strip().lower()
    return source, commit


class FixedFixtureRepository:
    """Acceptance transport for one fixed, immutable local HavoSec fixture only."""

    def __init__(self, source: Path, commit: str):
        self.source, self.commit = source.resolve(), commit
        self.git = GitRepository(30, 500_000)

    def _assert_target(self, snapshot):
        if snapshot.repository != FIXED_REPOSITORY:
            raise ValueError("Acceptance repository target is not the fixed HavoSec fixture")

    async def checkout(self, snapshot, workspace):
        self._assert_target(snapshot)
        return await self.git.checkout_revision(
            SimpleNamespace(repository=str(self.source)), workspace.repository,
            workspace.artifacts, self.commit,
        )

    async def checkout_revision(self, snapshot, destination, artifacts, commit_sha):
        self._assert_target(snapshot)
        if commit_sha != self.commit:
            raise ValueError("Acceptance source commit changed")
        return await self.git.checkout_revision(
            SimpleNamespace(repository=str(self.source)), destination, artifacts, commit_sha,
        )


class KnownGoodFixtureAgent:
    """Truthfully labelled deterministic proposal provider for this fixed fixture."""

    max_context_chars = 3000

    async def propose_remediation(self, finding, excerpt):
        if not str((finding.get("source_metadata") or {}).get("rule_id", "")).endswith(TARGET_RULE_SUFFIX):
            return None, {}
        if "eval" not in excerpt:
            return None, {}
        return RemediationProposal(
            summary="Replace eval with safe literal parsing",
            explanation="Parse supported Python literals without executing input.",
            affected_files=["app.py"], patch=PATCH.read_text(encoding="utf-8"),
            expected_security_effect="Removes arbitrary Python evaluation.",
            potential_side_effects=["Only Python literal syntax remains accepted."],
            recommended_tests=["Review accepted input formats."], confidence=1.0,
        ), {}


class ObservedRemediationWorkspace(RemediationWorkspace):
    observations: dict = {}

    def __exit__(self, *args):
        if self.paths and self.paths.original.exists():
            original_head, original_clean = git_state(self.paths.original)
            patched_head, patched_clean = git_state(self.paths.patched)
            self.observations.update(
                original_digest=tree_digest(self.paths.original),
                patched_digest=tree_digest(self.paths.patched) if self.paths.patched.exists() else None,
                original_head=original_head, original_clean=original_clean,
                patched_head=patched_head, patched_clean=patched_clean,
                workspace_root=str(self.paths.root),
            )
        result = super().__exit__(*args)
        if self.paths:
            self.observations["workspace_cleaned"] = not self.paths.root.exists()
        return result


async def demonstrate(email: str, password: str, report_path: Path | None = None):
    settings = DatabaseSettings.from_environment()
    client = create_database_client(settings)
    ids: dict[str, str] = {}
    result: dict = {}
    stage = "database connection"
    try:
        db = client[settings.database_name]
        await db.command("ping")
        app = acceptance_app(db)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://acceptance") as http:
            stage = "real superadmin authentication"
            login = await http.post("/api/admin/auth/login", json={"email": email, "password": password})
            if login.status_code != 200:
                raise RuntimeError(f"real login returned {login.status_code}")
            user = login.json()["user"]
            if user.get("role") != "superadmin":
                raise RuntimeError("a real superadmin account is required for disposable organization creation")
            headers = {"Authorization": "Bearer " + login.json()["token"]}

            async def call(method, path, expected=200, *, scoped=True, **kwargs):
                if scoped and ids.get("organization"):
                    path += ("&" if "?" in path else "?") + "organization_id=" + ids["organization"]
                response = await http.request(method, path, headers=headers, **kwargs)
                if response.status_code != expected:
                    detail = response.json().get("detail", "request failed") if response.content else "request failed"
                    raise RuntimeError(f"{method} {path.split('?')[0]} returned {response.status_code}: {detail}")
                return response.json()

            suffix = uuid4().hex[:10]
            stage = "disposable organization creation"
            organization = (await call("POST", "/api/admin/clients/", scoped=False, json={
                "name": "HavoSec Single Agent Runtime Verification " + suffix,
                "email": f"runtime-acceptance-{suffix}@havosec.com",
            }))["client"]
            ids["organization"] = organization["id"]

            with tempfile.TemporaryDirectory(prefix="havosec-acceptance-source-") as temporary:
                source, commit = create_fixture_repository(Path(temporary))
                source_digest = tree_digest(source)
                repository = FixedFixtureRepository(source, commit)
                grants = {ids["organization"]: frozenset({FIXED_REPOSITORY})}
                os.environ["PATH"] = str(SCANNER_BIN) + os.pathsep + os.environ.get("PATH", "")

                stage = "API domain creation"
                project = await call("POST", "/api/projects", 201, json={
                    "name": "Runtime remediation " + suffix,
                    "description": "Disposable single-agent remediation acceptance",
                })
                ids["project"] = project["id"]
                asset = await call("POST", "/api/assets", 201, json={
                    "project_id": project["id"], "name": "Owned vulnerable fixture",
                    "type": "repository", "target": FIXED_REPOSITORY,
                    "metadata": {"branch": "acceptance", "fixture": True},
                })
                ids["asset"] = asset["id"]
                run = await call("POST", "/api/security-runs", 201, json={
                    "project_id": project["id"], "asset_ids": [asset["id"]], "type": "standard",
                })
                ids["run"] = run["id"]
                if run["status"] != "queued":
                    raise RuntimeError("new security run was not queued")

                stage = "real discovery worker"
                worker = WorkerRepository(db, "runtime-acceptance-" + suffix, 960)
                claimed = await worker.claim(run["id"])
                if not claimed or claimed["status"] != "running":
                    raise RuntimeError("security run was not atomically claimed")
                discovery_root = {}

                class ObservedRunWorkspace(RunWorkspace):
                    def __exit__(self, *args):
                        if self.paths:
                            discovery_root["path"] = str(self.paths.root)
                        answer = super().__exit__(*args)
                        discovery_root["cleaned"] = bool(self.paths and not self.paths.root.exists())
                        return answer

                outcome = await SecurityPipeline(
                    worker, repository, SemgrepScanner(120, 4_000_000, 20),
                    partial(ObservedRunWorkspace, keep=False), grants,
                ).process(claimed)
                if outcome != "completed":
                    raise RuntimeError("discovery worker did not complete")

                stage = "finding API readback and validation"
                saved_run = await call("GET", "/api/security-runs/" + run["id"])
                findings = await call("GET", "/api/findings?security_run_id=" + run["id"] + "&limit=20")
                target = next((item for item in findings["items"] if
                               str(item.get("source_metadata", {}).get("rule_id", "")).endswith(TARGET_RULE_SUFFIX)), None)
                if not target:
                    raise RuntimeError("known eval finding was not returned by the API")
                ids["finding"] = target["id"]
                validation = await call("POST", f"/api/findings/{target['id']}/validate")
                if validation["status"] not in {"confirmed", "likely"}:
                    raise RuntimeError("deterministic validation did not make the finding eligible")

                stage = "remediation API creation and queue"
                remediation = await call("POST", "/api/remediations", 201, json={
                    "finding_id": target["id"], "summary": "Remove unsafe eval",
                    "recommendation": "Use ast.literal_eval", "acknowledge_likely": True,
                })
                ids["remediation"] = remediation["id"]
                queued = await call("POST", f"/api/remediations/{remediation['id']}/verify", 202)
                if queued["verification_status"] != "queued":
                    raise RuntimeError("remediation verification was not queued")

                stage = "real remediation worker"
                claimed_remediation = await worker.claim_remediation()
                if not claimed_remediation or str(claimed_remediation["_id"]) != remediation["id"]:
                    raise RuntimeError("queued remediation was not atomically claimed")
                ObservedRemediationWorkspace.observations = {}
                verification_outcome = await RemediationPipeline(
                    worker, repository, SemgrepScanner(120, 4_000_000, 20),
                    PatchApplicator(1_000_000),
                    partial(ObservedRemediationWorkspace, keep=False, max_bytes=10_000_000),
                    grants, timeout=180, patch_max_bytes=65_536, patch_max_files=1,
                    agent=KnownGoodFixtureAgent(),
                ).process(claimed_remediation)
                if verification_outcome != "verified":
                    raise RuntimeError("isolated remediation verification was not verified")

                stage = "final API and activity readback"
                final_remediation = await call("GET", f"/api/remediations/{remediation['id']}")
                final_finding = await call("GET", f"/api/findings/{target['id']}")
                events = await call("GET", f"/api/activity?project_id={project['id']}&limit=100")
                verification = final_remediation.get("verification_result") or {}
                observations = ObservedRemediationWorkspace.observations
                expected_events = {
                    "security_run_started", "findings_created", "security_run_completed",
                    "finding_validated", "remediation_created",
                    "remediation_verification_queued", "remediation_verification_started",
                    "remediation_verified",
                }
                event_types = {item["event_type"] for item in events["items"]}
                if not expected_events <= event_types:
                    raise RuntimeError("required lifecycle activity is missing: " +
                                       ", ".join(sorted(expected_events - event_types)))
                if final_remediation["status"] != "awaiting_approval" or final_remediation["verification_status"] != "verified":
                    raise RuntimeError("remediation did not reach the approval-ready verified state")
                if final_finding["status"] == "resolved":
                    raise RuntimeError("source finding was incorrectly resolved")
                if source_digest != tree_digest(source):
                    raise RuntimeError("immutable source repository changed")
                if observations.get("original_head") != commit or not observations.get("original_clean"):
                    raise RuntimeError("original remediation checkout changed")
                if observations.get("patched_head") != commit or observations.get("patched_clean"):
                    raise RuntimeError("patched workspace did not change")
                if not observations.get("workspace_cleaned") or not discovery_root.get("cleaned"):
                    raise RuntimeError("temporary worker workspace cleanup failed")

                result = {
                    "organization_name": organization["name"], "project_name": project["name"],
                    "commit": commit, "run": saved_run, "finding": final_finding,
                    "validation": validation, "remediation": final_remediation,
                    "verification": verification, "events": sorted(event_types),
                    "source_unchanged": True, "original_unchanged": True,
                    "patched_changed": True, "workspace_cleanup": True,
                }
    finally:
        if ids:
            db = client[settings.database_name]
            project_id = ids.get("project")
            organization_id = ids.get("organization")
            if project_id:
                for collection in PROJECT_CHILD_COLLECTIONS:
                    await db[collection].delete_many({"project_id": project_id})
                await db.projects.delete_one({"_id": ObjectId(project_id)})
            if organization_id:
                await db.client_companies.delete_one({"_id": ObjectId(organization_id)})
            remaining = 0
            if project_id:
                remaining += sum([await db[name].count_documents({"project_id": project_id})
                                  for name in PROJECT_CHILD_COLLECTIONS])
                remaining += await db.projects.count_documents({"_id": ObjectId(project_id)})
            if organization_id:
                remaining += await db.client_companies.count_documents({"_id": ObjectId(organization_id)})
            result["database_cleanup"] = remaining == 0
        client.close()

    finding, remediation, verification = result["finding"], result["remediation"], result["verification"]
    print("HAVOSEC SINGLE-AGENT REMEDIATION ACCEPTANCE")
    print("Organization:", result["organization_name"], ids["organization"])
    print("Project:", ids["project"], "-", result["project_name"])
    print("Asset:", ids["asset"])
    print("SecurityRun:", ids["run"], "status:", result["run"]["status"])
    print("Source commit:", result["commit"])
    print("Finding:", ids["finding"], "rule:", finding["source_metadata"]["rule_id"],
          "severity:", finding["severity"], "status:", finding["status"])
    print("Validation:", result["validation"]["status"], result["validation"]["confidence"],
          result["validation"]["validation_method"])
    print("Remediation:", ids["remediation"], "status:", remediation["status"])
    print("Proposal mode: deterministic-fixture")
    print("Verification:", verification["status"])
    print("Before findings:", verification["before_finding_count"])
    print("After findings:", verification["after_finding_count"])
    print("Target before: present")
    print("Target after:", "present" if verification["original_finding_present"] else "absent")
    print("New findings:", verification["new_findings_count"])
    print("Equal-or-higher regressions:", verification["new_equal_or_higher_findings_count"])
    print("VerificationResult ID: embedded (no separate collection ID)")
    print("Activity events:", ", ".join(result["events"]))
    print("Original repository modified: false")
    print("Original source checkout modified: false")
    print("Patched workspace modified: true")
    print("Workspace cleanup:", "passed" if result["workspace_cleanup"] else "failed")
    print("Database cleanup:", "passed" if result.get("database_cleanup") else "failed")
    if not result.get("database_cleanup"):
        raise RuntimeError("disposable database cleanup failed")
    print("SINGLE-AGENT REMEDIATION LOOP: COMPLETE")
    if report_path:
        report = {
            "decision": "SINGLE-AGENT REMEDIATION LOOP: COMPLETE",
            "ids": ids,
            "organization_name": result["organization_name"],
            "project_name": result["project_name"],
            "source_commit": result["commit"],
            "run_status": result["run"]["status"],
            "finding": {
                "rule_id": finding["source_metadata"]["rule_id"],
                "severity": finding["severity"], "status": finding["status"],
                "location": finding.get("location"), "fingerprint": finding.get("fingerprint"),
            },
            "validation": result["validation"],
            "remediation_status": remediation["status"],
            "proposal_mode": "deterministic-fixture",
            "verification": verification,
            "verification_result_id": None,
            "activity_events": result["events"],
            "source_unchanged": result["source_unchanged"],
            "original_checkout_unchanged": result["original_unchanged"],
            "patched_workspace_changed": result["patched_changed"],
            "workspace_cleanup": result["workspace_cleanup"],
            "database_cleanup": result["database_cleanup"],
        }
        report_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")


def credentials(args):
    email = args.email or os.environ.get("HAVOSEC_ACCEPTANCE_EMAIL") or input("Superadmin email: ").strip()
    password = os.environ.get("HAVOSEC_ACCEPTANCE_PASSWORD") or getpass.getpass("Superadmin password: ")
    if not email or not password:
        raise SystemExit("A real superadmin email and password are required")
    return email, password


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--email", help="Superadmin email; password is never accepted on the command line")
    parser.add_argument("--report", type=Path,
                        help="Optional sanitized JSON report path (contains no credentials or tokens)")
    arguments = parser.parse_args()
    if arguments.run:
        login_email, login_password = credentials(arguments)
        try:
            asyncio.run(demonstrate(login_email, login_password, arguments.report))
        except Exception as exc:
            raise SystemExit(f"SINGLE-AGENT REMEDIATION LOOP: NOT COMPLETE ({exc})") from exc
    else:
        print("Pass --run to execute the fixed disposable remediation acceptance lifecycle.")
