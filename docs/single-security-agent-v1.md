# Single Security Agent V1 — incremental delivery

## Current status

This milestone is not complete yet. Steps 1–5 of 6 are implemented: execution policy,
safe checkout/scanner adapters, deterministic normalization and the separate polling
worker lifecycle, one optional bounded analysis agent and live Assets/Runs/Findings
dashboard integration. Importing `security_engine` starts nothing. Execution and agent
enrichment remain disabled by default and no real repository scan or external AI request
has been run yet.

## Existing implementation reviewed

The completed MongoDB domain layer already provides organization-scoped Project,
Asset, SecurityRun, Finding, Remediation and Activity APIs with transactions and roles.
Those are reused. The dashboard Security Runs, Assets and Findings screens still import
demo fixtures. `frontend/src/stores/securityStore.js` is an unrelated static mock store.
`backend/routes/security.py` is an old optional n8n/multi-agent orchestrator route and
is not mounted by `server.py`; V1 will not activate or reuse it. No current LLM/provider
abstraction exists in the active backend. Git is available on PATH; Semgrep is not.

## Step 1 — authorization/configuration boundary

Added `security_engine/config.py` and `security_engine/policy.py`.

- `SECURITY_WORKER_ENABLED` defaults false. Agent and workspace preservation also
  default false. Polling, run/checkout/scanner/agent timeouts, maximum output (8 MB
  hard maximum), findings (2000 hard maximum) and agent count (50 hard maximum) are
  bounded and validated once from the environment.
- `SECURITY_REPOSITORY_GRANTS` is operator configuration: a JSON object mapping a
  canonical organization ObjectId string to at most 100 exact repository URLs.
  Example (not a default):
  `{"<organization-id>":["https://github.com/juice-shop/juice-shop"]}`.
  No wildcard/global grants are supported, and the development target is not hardcoded.
- V1 accepts credential-free public `https://github.com/<owner>/<repo>` URLs only.
  It rejects HTTP, SSH, credentials, ports, alternate hosts, query/fragment values,
  extra path components, encoded/traversal paths, whitespace and command-like input.
  `.git` and a trailing slash canonicalize to the same exact grant.
- A selected/default branch may come from metadata but is strictly bounded and rejects
  options, traversal, hidden/lock ref parts, control characters and shell punctuation.
  Other metadata—including `authorized`, `command` or future scanner options—has no
  effect on the immutable checkout snapshot.
- Authorization rechecks organization → active project → active repository asset,
  exact project relationship, asset type and the exact organization grant. It returns
  only organization/project/asset/provider/repository/branch. Errors are fixed safe
  messages and do not echo targets or credentials.
- This is an additional execution authorization boundary, not a replacement for JWT,
  role or API ownership checks. The worker must apply it again immediately before
  checkout because queued records and grants can change.

Step 1 tests: `venv\\Scripts\\python.exe -m pytest tests -q` — **243 passed**, four
preexisting warnings. Forty-five added cases cover fail-disabled defaults, exact
organization grants, ownership/type/status checks, URL and ref attacks, safe config
errors and bounds. No MongoDB record, frontend file or live index changed. No build,
clone, network request, dependency installation or scanner execution occurred.

## Remaining reviewable steps

2. **Completed:** Temporary workspace, safe Git checkout pinned to commit, Semgrep
   adapter, bounded raw result, deterministic normalization/fingerprint and fixture.
3. **Completed:** Atomic worker claim/lifecycle/cancellation, transactional finding
   upsert/activity, failure recovery and separate worker command.
4. **Completed:** One optional structured analysis agent/provider with
   injection/secret/context/cost boundaries and deterministic fallback.
5. **Completed:** Connect existing dashboard Assets/Runs/Findings screens and
   terminal-state polling; remove those screens' demo imports without redesigning the
   dashboard.
6. Full tests, dependency/setup docs and one real explicitly authorized demonstration.
   Juice Shop may be used manually after its exact organization grant is configured.

Do not describe V1 as operational until Steps 3–6 and the definition-of-done checks pass.

## Step 2 — isolated scanner and deterministic normalization

- `RunWorkspace` creates a unique OS-safe `havosec-run-*` directory containing only
  `repo` and `artifacts`. It removes the exact generated root on normal completion and
  exceptions. Preservation requires operator `KEEP_RUN_WORKSPACES=true`; no run/request
  field controls it. Cleanup of a process-killed host is not yet implemented.
- `GitRepository` resolves Git from PATH, runs fixed argument arrays with `shell=False`,
  disables credential helpers/prompts and uses shallow, no-tag, optional single-branch
  checkout. The authorized canonical URL/validated ref are positioned after `--`.
  A second fixed command verifies a 40-character commit SHA. URLs cannot contain
  credentials; Git output stays in the temporary artifacts and is not returned/logged.
- Shared external execution writes stdout/stderr directly to bounded artifact files
  rather than buffering unlimited output in pipes. It checks size every 100 ms and
  kills on the configured timeout/output limit. It passes a controlled environment.
  Current process termination targets the direct process; robust Windows/Unix process
  tree and OS-level CPU/memory/filesystem/network isolation remain Step 3 limitations.
- `SemgrepScanner` uses a single fixed `semgrep scan --json` argument list, metrics and
  update checks off, scanner working directory set to the repository, and the bundled
  `havosec-semgrep-v1` rules. It records version, timestamps, exit code, result/errors
  and configuration, caps output/results, and treats nonzero/invalid JSON safely.
  Raw JSON is a temporary ScannerResult/artifact, not copied into each Finding.
- The deliberately small rule file covers Python subprocess shell execution, Python
  eval and JavaScript/TypeScript eval. It is intentionally not a broad rule universe.
- The normalizer validates each structured result, ensures a repository-relative path,
  checks line ranges and maps ERROR→high, WARNING→medium, INFO→low and
  INVENTORY/EXPERIMENT/unknown→info. Findings remain candidates with confidence 0.7
  and status will remain new in persistence. The code snippet itself is not included
  in normalized evidence; only a SHA-256 plus scanner message/rule/location is kept.
- Fingerprint is SHA-256 over NUL-separated organization, project, asset, scanner,
  rule, repository-relative path, start line and snippet hash. It is deterministic
  across identical runs but intentionally is not sophisticated cross-line correlation.
- The local test fixture is one short Python file containing inert vulnerable source.
  Tests never import or execute it and external Semgrep/Git calls are mocked.

Semgrep is pinned in `requirements-worker.txt` rather than FastAPI's requirements.
An attempted install into the shared backend venv was stopped before installation when
resolution proposed replacing backend framework dependencies. `pip show` confirmed it
was not partially installed. Use an isolated tool/worker environment or pipx and expose
the resulting `semgrep` executable on the worker PATH.

Added workspace.py, executor.py, repository.py, scanners/base.py, scanners/semgrep.py,
normalization/semgrep.py, a bundled rule file, local fixture and engine execution tests.
Added `requirements-worker.txt` pinning Semgrep 1.176.0 separately from FastAPI.
The initial attempt to install it into the backend virtual environment was cancelled
before installation when dependency resolution showed it could upgrade FastAPI-shared
packages. `pip show semgrep` confirms it was not installed. This separation avoids
coupling the control plane to the tool's Python dependencies; install it in an isolated
tool/worker environment in Step 3. Backend requirements remain unchanged.

Final verification: `venv\\Scripts\\python.exe -m pytest tests -q` — **260 passed**,
four existing warnings. Tests cover grants, URL/ref/path attacks, ownership, cleanup,
bounded timeout/output handling, fixed process arguments, malformed scanner JSON,
severity mapping and fingerprints. No clone, external scan, live DB mutation or frontend
build ran. Semgrep remains unavailable on PATH, so no real scan is claimed yet.

## Step 3 — worker lifecycle and result persistence

- `python -m security_engine.worker` is a standalone polling process. It is not imported
  or started by FastAPI and exits safely unless `SECURITY_WORKER_ENABLED=true`.
- Each worker has a unique ID and transactionally claims the oldest queued run with one
  conditional `find_one_and_update`. The run receives a renewable lease, start time,
  progress and a `security_run_started` activity event in the same transaction. Two
  workers cannot claim the same queued record.
- Immediately before checkout, the worker reloads the run's project, single repository
  asset and requester. It rejects deleted/cross-organization/inactive records, changed
  relationships, non-admin requesters and repositories no longer present in the exact
  organization grant. Superadmins remain platform-scoped; admins must still belong to
  the run organization.
- Progress is stored only at meaningful boundaries: checkout, scanner start, scanner
  completion, normalization and persistence. Each heartbeat conditionally requires the
  same running run and worker ID, refreshes the lease and fails closed if ownership or
  status changed. Cancellation is checked around all major stages and immediately before
  the transactional result commit.
- Successful persistence transactionally upserts normalized findings, stores one bounded
  raw scanner record, conditionally completes the owned run and inserts findings/completion
  activity. Findings deduplicate by organization plus deterministic fingerprint while
  retaining the first, last and bounded run association list, so a repeated result remains
  queryable from each run.
- Expired worker leases are transactionally changed to failed one at a time and receive
  a `security_run_failed` event. Known dependency, timeout, output and policy failures map
  to fixed safe text; unexpected details stay in structured server logging and are not
  returned in run errors. Workspaces still clean up through the context manager.
- New explicit indexes enforce tenant-scoped fingerprint and raw-result uniqueness and
  expire raw scanner results after 30 days. Index definitions were tested but have not
  been applied to the live database in this step.
- The worker remains deterministic-only. `analysis_mode` is recorded as
  `deterministic_only`, `agent_enriched` is zero, and no LLM/provider is called. Step 4
  will add the single optional bounded analysis agent with scanner-only fallback.

Added `security_engine/storage.py`, `pipeline.py`, `worker.py`, worker lifecycle tests,
run metadata fields, repeat-run finding associations and activity types. Final backend
verification: `venv\\Scripts\\python.exe -m pytest tests -q` — **281 passed**, four
existing warnings. Git and Semgrep processes are mocked in tests; no clone, scan, live
database mutation, frontend build or `dist` creation occurred.

## Step 4 — one optional bounded analysis agent

- `FindingAnalysisAgent` is the only agent. It has no tools and cannot run commands,
  edit files, apply remediation, access unrelated targets or create findings. It can
  only enrich a bounded prefix of deterministic Semgrep candidates sequentially.
- `AnalysisResult` is strict Pydantic output with title, description, category,
  confidence, risk summary, remediation guidance and priority. Extra fields, invalid
  confidence and malformed/free-form provider responses are rejected. Scanner severity,
  fingerprint, location and evidence remain deterministic and cannot be replaced by AI.
- Repository paths, scanner messages and source excerpts are explicitly labelled as
  untrusted JSON data in the prompt. System instructions say to ignore embedded
  instructions, avoid tools/exploitation and return only the schema. The complete
  repository, README files and unrelated source are never sent.
- Context is character-bounded. Sensitive paths (`.env*`, key stores, credential/secret
  directories and common private-key files) omit excerpts. Common private-key, bearer,
  API-key, password, GitHub, OpenAI, AWS, Slack and JWT patterns also cause source and
  scanner-message omission. This is a conservative V1 safeguard, not a complete secret
  classification system.
- `AnalysisProvider` isolates provider transport. The first adapter uses the fixed
  OpenAI HTTPS endpoint, strict JSON Schema output, no redirects, operator-selected
  validated model name, a configured timeout and a 64 KiB streamed response ceiling.
  API keys come only from `OPENAI_API_KEY`, are secret-wrapped and never put in prompts,
  summaries, logs or database records.
- Agent execution requires `AGENT_ENABLED=true`, a key and a nonzero
  `MAX_AGENT_FINDINGS_PER_RUN`; otherwise the pipeline is scanner-only. Any request,
  timeout or validation error falls back per finding without failing the run. Run and
  finding metadata distinguish `deterministic_only` from `agent_enriched`; summaries
  contain only aggregate token counts returned by the provider.
- Sending any source excerpt to a hosted provider is an explicit operator opt-in and is
  subject to that provider's data handling. Private-repository support remains out of
  scope, and future deployments should add organization-specific consent, regional/data
  retention controls and a stronger secret classifier before enabling enrichment.

Added `security_engine/agents/analysis.py`, `agents/provider.py` and focused tests;
updated worker wiring, progress (80% analysis), run summary/mode and finding analysis
metadata. Final backend verification: `venv\\Scripts\\python.exe -m pytest tests -q`
— **291 passed**, four existing warnings. Provider transport was tested with an
in-memory HTTP transport; no external AI call, Git checkout, Semgrep scan, live database
mutation, frontend build or `dist` creation occurred.

## Step 5 — live dashboard execution views

- Added one authenticated `securityApi` adapter for the existing Assets, Security Runs
  and Findings endpoints. The three execution screens no longer import demo projects,
  assets, runs, findings, reconnaissance or remediation data.
- Assets list/detail now show real organization-scoped records and real findings for a
  selected asset. Empty and error states avoid claiming that an empty list proves safety.
- Security Runs now list real queue records, progress, timestamps, commit, scanner,
  analysis mode, safe failure text and summary counts. Admins can queue a single active
  repository asset and cancel an active run; users remain read-only and backend role
  enforcement remains authoritative.
- Run detail loads its related asset and findings through scoped endpoints. Queued and
  running records poll every three seconds; polling stops at completed, failed or
  cancelled. Transient polling retries are capped, timers are cleaned up on navigation,
  and users can retry visible failures manually.
- Findings now use real server filters for project, severity and status, show scanner
  evidence separately from optional agent analysis, link to the latest associated run,
  and permit admins to update only the existing finding lifecycle status. The previous
  demo proof-of-concept and local remediation-draft UI was removed from this screen.
- Live project links use a query filter on the top-level Findings route so they do not
  depend on the older demo-backed Projects shell. Migrating Projects, Overview,
  Remediation and Activity to their domain APIs is intentionally outside this narrowly
  scoped step and remains visible as separate product work.

Added `services/securityApi.js`, `hooks/usePollingResource.js`, `ResourceState.jsx`,
run status constants and API presentation tests; updated the three screens and small
responsive form/filter styles. Changed files pass ESLint. Frontend verification:
`vitest --run` — **12 files, 42 tests passed**. No frontend build ran and `frontend/dist`
remains absent. Browser/API integration was not claimed because no authenticated manual
session was exercised during this step.

## Step 6 — operational verification and authorized demonstration

- Provisioned all 23 domain indexes in the configured business database and verified
  the real JWT, MongoDB lifecycle, organization isolation, role checks and transaction
  rollback in a fresh isolated database that was removed after the test.
- Installed Semgrep 1.176.0 in `backend/.tools/semgrep-venv`, separate from the FastAPI
  environment. The local tool directory is ignored by Git and does not change backend
  runtime dependencies.
- Added `verify_security_cycle.py`, an explicit one-shot operator command. It accepts no
  repository input: the manual target is fixed to the official public OWASP Juice Shop
  repository and authorization is scoped to the selected organization. It creates the
  Project, repository Asset and queued SecurityRun through authenticated APIs, claims
  only that exact run, executes the ordinary pipeline, and reads the saved run/findings
  back through the same scoped APIs.
- The live database had no valid customer membership. The verification therefore used
  the existing active superadmin and created a dedicated active `HavoSec V1 Verification`
  organization through the existing platform organization API. It did not rewrite or
  infer any user membership.
- The first live pass exposed a Windows-specific cleanup defect: a read-only Git pack
  index prevented `shutil.rmtree`. Cleanup now clears the mode only for the file whose
  deletion raised `PermissionError`, retries that operation, and still propagates all
  other failures. The exact leftover temporary directory was removed and the corrected
  live pass cleaned its workspace successfully.

Final real demonstration:

- Repository: `https://github.com/juice-shop/juice-shop`
- Project: `6a99c84de84263e43cd0f95d` (`HavoSec V1 Authorized Demo e7f396d7`)
- Asset: `6a99c84de84263e43cd0f95f`
- SecurityRun: `6a99c84ee84263e43cd0f961`
- Commit: `1618a611b173b4bf114028e6e02549950606e29d`
- Scanner: Semgrep `1.176.0`, bundled `havosec-semgrep-v1` rules
- Results: 2 raw, 2 normalized, 2 accessible through the scoped Findings API
- Analysis: deterministic only, 0 agent-enriched (no provider key was configured)
- Severity: 0 critical, 0 high, 2 medium, 0 low, 0 info
- Final status: `completed`; start, findings-created and completion activity persisted
- Temporary workspace: cleaned

Final regression verification: `venv\Scripts\python.exe -m pytest tests -q` —
**292 passed**, four existing warnings. No frontend build ran and `frontend/dist`
remains absent.
