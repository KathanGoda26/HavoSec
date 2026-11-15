# Backend domain milestone — incremental delivery

## Scope and current status

MongoDB stays. No worker, scanner, queue, LLM, autonomous patching or frontend API
integration is added. **Increments 1–6 are implemented and the live isolated lifecycle
verification has passed.** Domain indexes were created/verified on the configured
database. Existing documents have not been migrated automatically. Earlier blocker
notes below are historical; see the final verification follow-up.

## Inspection

The findings below describe the initial audit; increment notes identify resolved items.

Reviewed server registration/lifespan, models/schemas.py, routes, auth/roles helpers,
seeding and account migration scripts, notifications, architecture and existing tests.

- Most routes use Motor through app.state.db, but queries live in handlers.
- client_companies / ClientCompany already represent organizations. Reuse that
  collection and preserve contact, subscription, services and isActive fields.
- users is the shared identity collection. JWT decoding reloads identity from it;
  serialize_user exposes organizationId from legacy aliases.
- No persisted Project/Asset/SecurityRun/Finding/Remediation domain APIs exist yet.
- Architecture uses a separate synchronous MongoClient, MONGODB_URI and fixed DB.
  It reads legacy executions/agent_results/vulnerabilities and synthesizes components.
  Keep compatibility but migrate its database adapter separately; do not confuse it
  with future authoritative SecurityRun observations.
- client_dashboard remains a legacy security_events API with invented uptime/response
  numbers. Plan a compatible domain overview with null security score, not fake telemetry.
- Startup previously seeded content and could seed weak-password demo accounts when
  enabled. Startup also printed the Mongo URL, potentially including credentials.
- Customer admins currently have global client-management/CMS/SEO access. Client
  routes have unrestricted updates and hard deletion. These require platform-only
  guards and organization lifecycle changes before claiming full tenant isolation.
- Notifications are recipient-scoped for reads, but admin creation can target any
  user; WebSocket activity checks and admin broadcast targeting need review.
- Legacy auth admin-login differs from client-login lockout behavior. Legacy dates,
  pagination bounds, raw ObjectId conversion and error handling are inconsistent.
- Blog slug fallback can bypass published-only filtering. Public/CMS boundaries
  require a focused compatibility/security increment, not a claim that all legacy
  endpoints became safe through the new ownership helper.
- security.py is not registered by server.py; leave orchestration disabled. Its
  dynamic `core.*` imports conflict with the backend core namespace if re-enabled;
  enabling/refactoring that optional engine is outside this milestone.

## Increment 1 implemented

- core/database.py: backend-relative .env loading (process env wins), secret-safe
  configuration representation, shared Motor factory and database dependency.
- server.py: uses this configuration; never seeds business data on startup; closes
  client in finally; no connection URL printed. Five-second server selection timeout.
- seed_db.py: retains the explicit seed entry point with shared config and guaranteed
  cleanup. It was NOT run. Legacy seed implementation still needs account hardening.
- core/ids.py: new-domain ObjectId parsing and canonical string IDs; malformed values
  return controlled 404. Existing document IDs are untouched.
- repositories/organizations.py: reads client_companies, no duplicate collection.
- core/ownership.py: new-domain organization resolver checks membership, existence
  and active state. Customer organization selectors are rejected; superadmin must
  explicitly select one organization through a service permitting that operation.
  Scope queries cannot override organization_id. Missing assignments fail closed.
- These helpers are not yet wired to new domain routes (none created this increment).
  Legacy auth/session behavior is deliberately unchanged.

## Data and migration considerations

No live database writes, indexes, deletions or account/password changes were performed.
The consolidation script generates an organizationId for demo customers without
creating a matching client_companies record. Do not run that script again: it also
rotates passwords and can drop admin_users. Inventory assignments with a dry-run
migration before wiring new customer APIs; establish explicit approved mappings.
Do not group users by company display text or silently grant access to another tenant.

Future domain documents use canonical string relationship IDs and UTC-aware timestamp
creation. Legacy datetime decoding remains unchanged because password-reset code
currently compares naive datetimes. New repositories must handle UTC consistently.

## Verification

Command from backend: `venv\\Scripts\\python.exe -m pytest tests -q`.
Initial sandbox execution could not access WindowsApps Python; rerun with approval.
Result: **26 passed**, including 19 new foundation cases. Four existing dependency/
legacy Pydantic/datetime warnings remain. The test suite imported FastAPI/server and
exercised lifespan with a mocked database client: no business collections were touched.
This is not live MongoDB integration or full HTTP domain authorization verification.
The running server was not restarted; restart is needed to load changes if not using
reload. No frontend build was run.

## Subsequent reviewable increments

1. Organization compatibility, dry-run migration tooling and platform/client RBAC — implemented below; account mapping awaits an explicit decision.
2. Project + Activity foundation: validated schemas, service/repository split,
   bounded pagination, archive semantics and ownership-aware HTTP tests.
3. Assets + Security Runs: relationship checks, cancellation state transitions,
   persistence only; no execution.
4. Findings + Remediation: bounded structured evidence, internal finding ingestion,
   managed lifecycle with no patch execution.
5. Domain overview, explicit indexes, legacy adapter integration and isolated
   end-to-end API tests. Security score unavailable until a real model exists.

For each slice, add tests proving unauthenticated rejection, read-only user policy,
tenant isolation and invalid cross-resource references before connecting the frontend.
Use an isolated test database for the full project → asset → run → finding →
remediation → activity lifecycle. Final milestone report will inventory schemas,
endpoints, indexes, migrations and files when those slices are implemented.

Files added: core/__init__.py, core/database.py, core/ids.py, core/ownership.py,
repositories/__init__.py, repositories/organizations.py, tests/test_domain_foundation.py,
and this document. Files modified: server.py, seed_db.py. Files deleted: none.

## Increment 2 — organization compatibility and platform permissions

- Reused /api/admin/clients and client_companies; no duplicate organization collection
  or parallel CRUD API. Added PATCH alongside legacy PUT. Response envelopes retained.
- Added models/organizations.py, services/organizations.py and extended the repository.
  Create/update inputs reject unknown and server-controlled fields, invalid status,
  conflicting status/isActive and null mandatory fields. List limit is 1–100, offset
  is 0–100000. IDs are validated centrally by the repository.
- New records receive ID-suffixed slugs and UTC-aware timestamp creation, with legacy
  createdAt/updatedAt mirrored. Existing contact/subscription/service fields survive.
  Read adapters supply missing metadata without silently updating legacy documents.
- DELETE now deactivates, never deletes a company or its history. Explicit status or
  isActive changes synchronize both fields. Atomic find_one_and_update returns results.
- Global client management, admin dashboard, content/blog/SEO mutations, demo-request
  management, uploads management and notification creation now require superadmin.
  Route-level guards also protect public aliases of those write endpoints. Public
  read endpoints and demo form submission remain unchanged. Admin login compatibility
  still accepts admin; customer dashboard reads are unchanged.
- Membership aliases normalize ObjectId casing and reject conflicting assignments
  when serializing users. Login is not blocked; new organization services fail closed.
- Added audit_organizations.py: read-only preflight with minimal projections; no
  --apply option, no guessed mapping, no role changes, no password changes or writes.

### Live migration preflight

Executed `venv\\Scripts\\python.exe audit_organizations.py` with approval against
configured MongoDB. Result: zero valid customer assignments, one missing assignment
and two dangling assignments. The two dangling accounts reference the same missing
organization. No metadata backfill candidates were reported. No database data changed.
An explicit organization/account mapping is required before wiring customer domain
APIs; do not infer membership from names or rerun the password-rotating consolidation.

### Tests and activation

Added tests/test_organizations.py: HTTP unauthenticated/customer rejection on all
client CRUD methods; superadmin read/create/deactivate; validation, pagination, safe
DB errors; non-mutating legacy adapters and audit; public-alias guard checks.
Full command `venv\\Scripts\\python.exe -m pytest tests -q`: **73 passed**, four
previous warnings. Tests use in-process HTTP and mocked repositories, not live CRUD.
No build or migration writes. Running backend was not restarted by this increment;
restart it if not using reload to activate the new API behavior.

Increment 2 added core/membership.py, models/organizations.py, services/__init__.py,
services/organizations.py, audit_organizations.py and tests/test_organizations.py.
Modified repositories/organizations.py, routes/clients.py, utils/auth.py, server.py,
and guards in routes/content.py, blog.py, demo_requests.py, seo.py, uploads.py and
notifications.py. No files deleted or indexes created.

Remaining legacy risks: organization_scope sentinel behavior, architecture's separate
database adapter, notification WebSocket/broadcast policy, password-reset/verification
authorization, and public blog slug fallback. This slice does not certify the entire
legacy backend as tenant-isolated. Domain lifecycle and per-resource HTTP tests follow.

## Increment 3 — Projects and product activity

Implemented organization-scoped POST/GET `/api/projects`, GET/PATCH/DELETE
`/api/projects/{project_id}`, and GET `/api/activity`. No legacy dashboard contracts
were replaced and no frontend changes or builds were made.

- Admin can create, edit and archive projects in their assigned active organization;
  user is read-only. Superadmin must explicitly select one organization using the
  `organization_id` query parameter. Customer-supplied organization selectors fail
  with 403. Missing/dangling/inactive memberships also fail closed.
- Project input accepts name (1–200 trimmed characters), description (up to 4000).
  Ownership, author, status and UTC dates are server-controlled. PATCH edits name
  and description only. DELETE archives; repeated archive succeeds without another
  event. Archived projects remain readable and cannot be edited or restored yet.
- Every lookup and update includes organization ownership. Foreign project IDs
  return 404, including when filtering activity. Lists return `items`, `total`,
  `limit`, `offset`; defaults 50/0, bounds 1–100/0–100000. Projects optionally filter
  active/archived status; activity optionally filters project_id. Default project
  lists include archived records. Sorting uses descending created_at and _id.
- Activity records hold organization/project/actor/entity IDs, event type, a fixed
  message, changed-field metadata and UTC created_at. No public write endpoint.
  Project create/update/archive generate events; this is product history, not an
  immutable security audit system.
- Project writes and activity insertion share a MongoDB transaction with the driver's
  transaction retry handling. **Atlas or a transaction-capable replica set/sharded
  deployment is required.** Standalone MongoDB cannot perform these writes; failures
  return a controlled 503. There is no unsafe nontransactional fallback. Transaction
  failures are not assumed to prove rollback after an ambiguous network commit result;
  clients should refresh before manually retrying a create. Request idempotency keys
  are not implemented in this increment.
- BSON IDs stay ObjectIds internally and serialize to strings. New timestamps are
  timezone-aware; legacy naive BSON UTC dates are normalized for these API responses.
- Index provisioning is deferred to increment 6. Evaluate projects:
  organization_id/created_at/_id and organization_id/status/created_at/_id;
  activity_events: organization_id/created_at/_id and
  organization_id/project_id/created_at/_id. No indexes or live records changed.

Added models/projects.py, models/activity.py, core/domain_api.py,
repositories/projects.py, repositories/activity.py, services/projects.py,
services/activity.py, routes/projects.py, routes/activity.py and tests/test_projects.py.
Modified server.py to mount the new routes. No files deleted.

Verification: `venv\\Scripts\\python.exe -m pytest tests -q` — **113 passed**, four
existing warnings. Forty new tests exercise real routes/services/repositories with
an in-memory transactional database double: lifecycle/history, tenant isolation,
RBAC, validation, paging, explicit platform scope, and simulated event-write rollback.
Main application import/route registration and existing lifespan tests pass. This is
not live MongoDB transaction verification; that remains an integration check in
increment 6. No server restart performed.

User identified the previously audited accounts as dummy data and asked to continue.
They remain untouched; valid organization membership is still required before those
customer accounts can call the new APIs. No guessed membership or migration applied.

Three increments remain: 4 Assets/Security Runs, 5 Findings/Remediation,
6 Overview/index provisioning/integration lifecycle verification.

## Increment 4 — Assets and Security Runs

Added `/api/assets` POST/GET, `/api/assets/{asset_id}` GET/PATCH/DELETE,
`/api/security-runs` POST/GET, `/api/security-runs/{run_id}` GET, and
`/api/security-runs/{run_id}/cancel` PATCH. Existing frontend endpoints remain unchanged.

- Admin manages within their organization; user reads only. Superadmin uses the
  same explicit single-organization query selector as Projects. Foreign resource
  IDs and project filters fail with 404; ownership is never accepted in request bodies.
- Asset types: repository/application/domain/api/host. Name and target have bounds
  of 200/2048 characters; metadata is a JSON object capped at 16 KiB encoded size.
  Targets are stored only, never fetched or executed. No scanner-specific validation
  or network access occurs. PATCH allows name/target/metadata, not project/type/owner.
  DELETE archives and preserves history. Repeated archive is idempotent.
- Runs require 1–100 unique asset IDs in the selected active project/organization.
  Types are quick/standard/full. Creation persists queued status, zero progress and
  null started_at/completed_at/summary/error; requested_by and ownership are derived.
  There is no queue, execution, scanner or fabricated result. Future workers will
  need lifecycle integration; none is mounted or activated by this change.
- Cancellation is permitted for queued/running runs, idempotent for cancelled runs,
  and rejected for completed/failed runs. Conditional writes prevent cancellation
  from overwriting a concurrently completed run. Cancellation timestamps completion
  without claiming successful work. It remains allowed when the project is archived.
- Archived projects cannot accept asset changes or new runs. Existing children remain
  readable. There is no cascading deletion/cancellation. Historical run asset IDs stay
  linked after asset archive; target snapshots are not part of this increment.
- New writes and product activity share transactions. Parent project and referenced
  asset write guards recheck active ownership inside the transaction and increment an
  internal `_relationship_version` counter. This serializes against concurrent archive
  instead of relying only on a preflight read. Counters are excluded by API response
  schemas. As in Step 3, a transaction-capable MongoDB deployment is required.
- New asset_created/updated/archived and security_run_created/cancelled activity types.
  Lists use the existing items/total/limit/offset contract, bounds, and stable ordering;
  project_id and status are optional filters. Archived records remain in default lists.

Files added: models/assets.py, models/security_runs.py,
repositories/project_resources.py, services/project_resources.py, routes/assets.py,
routes/security_runs.py, tests/test_assets_runs.py. Modified models/activity.py,
server.py and the existing isolated database double in tests/test_projects.py.
No files deleted, build run, account mutation or server restart.

Verification: `venv\\Scripts\\python.exe -m pytest tests -q` — **161 passed**, four
existing warnings (48 tests added). Tests exercise actual routes/services/repositories
against isolated transaction doubles: lifecycle, no-execution defaults, tenant and
project boundaries, authentication/RBAC, metadata/ID validation, bounded lists,
archive/cancel rules, simulated concurrent state changes and rollback on event failure.
Real MongoDB concurrency/transaction verification remains for the integration step;
test doubles are not evidence of live replica-set behavior.

Index candidates for Step 6: assets and security_runs each need scoped project/status
and creation-order indexes based on their list filters. No indexes applied here.
Existing dummy accounts still need valid organization assignments for customer APIs.

Two increments remain: 5 Findings/Remediation; 6 Overview, indexes and live-isolated
integration lifecycle verification (with explicit safe test-database configuration).

## Increment 5 — Findings and Remediation

Added GET `/api/findings`, GET/PATCH `/api/findings/{finding_id}`, POST/GET
`/api/remediations` and GET/PATCH `/api/remediations/{remediation_id}`.
No finding-creation HTTP endpoint, scanning, command execution or repository changes.

- FindingResponse defines structured title/description/category, severity, CVSS 0–10,
  confidence 0–1, status, component/location, source, optional asset/run references,
  evidence/source metadata and detection/creation/update timestamps. JSON objects are
  bounded to 64 KiB each; references to 100 entries of 2048 characters each. This is
  the trusted ingestion/response contract, not an implemented ingestion service.
  Fixtures validate it before inserting test findings. Future ingestion must validate
  relationships and persist finding_created activity transactionally; merely adding
  the event constant does not implement ingestion.
- Finding PATCH accepts status only: new/triaged/confirmed/remediating/resolved.
  Admin can manually reclassify or reopen; there is no forced scanning workflow.
  Severity, evidence, provenance and ownership cannot be rewritten via this API.
- Finding list filters: project_id, asset_id, security_run_id, severity, status.
  Related records are checked against the organization and project, including the
  asset's membership in a referenced run. Inconsistent legacy/directly inserted
  relationships fail closed with 404 rather than returning a partial detail record.
- Remediation create accepts finding_id, summary (2000), recommendation (16000),
  proposed_fix (32000). Organization/project are derived from the finding. Initial
  state is pending, created_by is authenticated, approved_by is null. Content is
  stored as text only, never executed. Multiple proposals per finding are allowed.
- Remediation list supports project_id, finding_id and status filters. Ownership
  and finding/project relationships are validated for detail and list results.
- Human-managed transitions: pending → in_progress/awaiting_approval/rejected;
  in_progress → pending/awaiting_approval; awaiting_approval → pending/approved/rejected;
  approved → pending/resolved; rejected/resolved → pending. Proposal text cannot
  change while approved/rejected/resolved, or while awaiting approval unless returned
  to pending. Approval and proposal editing cannot be combined in one request.
- approved_by is set from the acting admin on approval, retained on resolution and
  cleared on reopening. There is no separate two-person approval requirement in this
  initial role model. Approval/resolution is a manual record, not proof of a deployed
  fix; neither automatically marks the related finding resolved.
- Existing role/scope rules apply: user reads, admin manages own organization,
  superadmin explicitly selects a single organization. Archived projects remain
  readable but reject mutations. No-op updates do not duplicate activity.
- finding_updated and remediation_created/updated events save in the same transaction
  as their changes. Shared resource updates now compare both status and updated_at,
  rejecting in-flight stale writes with 409. This is not an HTTP ETag/If-Match feature
  for detecting a browser's stale view before the request begins.
- Common bounded pagination and UTC response normalization are preserved. Transaction
  requirements and ambiguous-commit caveats from Step 3 still apply. Parent project
  guards remain inside writes; no relation IDs can be changed via these endpoints.

Added models/findings.py, models/remediations.py, services/findings.py,
services/remediations.py, routes/findings.py, routes/remediations.py,
tests/test_findings_remediations.py. Reused ProjectResourceRepository rather than
duplicating collection access; updated its conditional update filter, models/activity.py
and server.py route registration. No files deleted or frontend build run.

Verification: `venv\\Scripts\\python.exe -m pytest tests -q` — **192 passed**, four
existing warnings. 31 added tests cover the fixture finding → status → remediation →
approval/history flow, organization and project boundaries, authentication/RBAC,
controlled fields, filters, size limits, archive behavior, transaction rollback and
in-flight approval conflicts. Tests use isolated transaction doubles, not live MongoDB.
Existing accounts/data were not modified and no backend server restart was performed.

List relationship checks deliberately favor correctness for now and issue extra
bounded lookups (up to 100 records); evaluate batching when optimizing real datasets.
Index provisioning remains Step 6: assess organization/project/severity/status/date
filters for findings and organization/project/finding/status/date for remediations.

One increment remains: Overview (score unavailable), explicit indexes, and isolated
MongoDB integration/lifecycle verification. Legacy risks listed earlier remain outside
the new domain API guarantees; no blanket security certification is implied.

## Increment 6 — Overview, index definitions and integration harness

Added GET `/api/domain/overview` with the shared authentication/organization boundary
and optional project_id filter. This intentionally does not replace the existing
`/api/dashboard/overview`, whose legacy payload is still consumed by the frontend.
The legacy endpoint still has its previous placeholder uptime; the new endpoint does
not publish uptime or fabricated telemetry. Frontend integration remains separate.

The new overview returns:

- security_score null and security_score_status unavailable;
- persisted record counts for projects/assets/runs/findings/remediations (including
  archived records), open findings (all defined statuses except resolved), and open
  critical findings;
- severity_counts across all finding states, latest run, and at most five recent
  findings/runs/activity entries each. Latest run means newest created, not completed.

Counts are scoped database queries, not estimates. Independent queries are not a
single snapshot, so counts/recent lists can differ briefly during concurrent writes.
No scoring algorithm or live-monitoring claim is introduced.

### Index definitions and explicit application

core/domain_indexes.py defines 20 non-unique indexes across six domain collections:

- organization_id/created_at/_id for all six, supporting stable recent lists;
- organization_id/project_id/created_at/_id for the five child collections;
- organization_id/status/created_at/_id for the five status-bearing collections;
- findings organization_id/severity/status, organization_id/asset_id and
  organization_id/security_run_id for counts/reference filters;
- remediations organization_id/finding_id for proposal lists.

Existing _id indexes remain. No uniqueness/backfill assumption is made about existing
data. The definitions total 20 indexes (6 + 5 + 5 + 3 + 1).
Compound combinations not covered can use the scoped prefix and filter/sort in memory;
measure production query plans before adding more indexes.

`venv\\Scripts\\python.exe manage_domain_indexes.py` prints definitions without
connecting. `... manage_domain_indexes.py --apply` explicitly creates/verifies them
on configured DB_NAME. It is not called at startup and was **not run against the
business database** in this increment. Live provisioning remains pending.

### Verification results and blocker

`venv\\Scripts\\python.exe -m pytest tests -q`: **197 passed**, four existing
warnings. New tests cover overview counts/empty scope/foreign project access,
authentication, controlled database errors, bounded recent activity and index specs.
Existing import/lifespan tests pass. These are isolated fixtures, not live verification.

Added explicit `verify_domain_integration.py --run`. It chooses a fresh
havosec_test_<uuid> database, rejects a preexisting target, creates indexes twice,
uses real JWT/database account lookup through in-process HTTP, runs project → asset →
queued run → trusted fixture finding → remediation → activity/overview, checks
cross-organization/role failures and forces a real transaction rollback via a duplicate
event ID. In finally it drops only its generated database, never configured DB_NAME.
Without --run it performs no network connection or write. It does not test browser
login/password entry or start a listening web server.

Attempted the verifier with user approval. Atlas returned OperationFailure code 8000
at the initial database-access check, before creation of the test database. Retried
with safe error classification; the result remained Atlas rejection, not a confirmed
authentication-specific error. No test database was created or removed, no business
records changed, and no live indexes were applied. Credentials/topology were not
printed. **Live lifecycle, live rollback and index application are NOT verified.**
Resolve the configured MongoDB server access/permissions in Atlas, then rerun this
isolated verifier and explicitly apply the business-database indexes. Do not report
the entire milestone complete until these checks succeed.

### Files and handoff

Added models/overview.py, repositories/overview.py, services/overview.py,
routes/domain_overview.py, core/domain_indexes.py, manage_domain_indexes.py,
verify_domain_integration.py and tests/test_domain_overview.py. Modified server.py
to mount the new summary route and test_projects.py's test database mapping helper.
No files deleted, no frontend build, frontend/dist remains absent, no server restart.

All domain schemas, role boundaries and API changes are described in increments 1–5
above. Organization storage reuses client_companies; users remain the account source.
Routes/services/repositories were added incrementally rather than renaming the tree.
At the initial Step 6 handoff, indexes and live verification were still pending;
the follow-up below records their completion.
Before any security worker work, also address documented legacy authorization risks,
valid customer memberships, trusted finding ingestion, idempotency/ambiguous writes,
worker lifecycle/cancellation semantics and real query-plan/concurrency checks.

## Final verification follow-up — completed

After the user confirmed database connectivity, read-only ping, configured collection
listing and server database listing all succeeded. Adding stage-aware, redacted errors
identified the earlier code 8000: the verifier generated a 45-byte test database name,
but this Atlas environment accepts at most 38 bytes. This was a **verification-script
bug**, not evidence of invalid database credentials or missing permissions. The earlier
claim that rejection occurred at the initial access check was incorrect: it occurred
at isolated index provisioning; cleanup also rejected the invalid database name.

Fixed the generated name to a 37-byte havosec_test_ prefix plus 24 random hexadecimal
characters. Kept collision and configured-database exclusion checks. Added a regression
test for name length and distinctness and safe stage-aware error reporting.

With approval, `venv\\Scripts\\python.exe verify_domain_integration.py --run` passed
against real MongoDB: real JWT/account lookup, full persisted domain lifecycle,
organization isolation, role checks, index creation/repeat application and forced
transaction rollback. The exact generated test database
`havosec_test_4ac9e483ec824f728ea49e82` was then dropped successfully. Only synthetic
test records were removed; this cleanup is not intended to be recoverable. Existing
business records and credentials were not changed.

With approval, `venv\\Scripts\\python.exe manage_domain_indexes.py --apply` succeeded
on configured DB_NAME, creating/verifying all 20 planned non-unique indexes across
projects, assets, security_runs, findings, remediations and activity_events. This can
also create empty domain collections when they do not already exist. No business
records were added, altered or deleted by index application.

The live harness uses in-process HTTP and persisted test accounts/tokens, not browser
password login or load testing. It verifies transaction rollback but is not a production
concurrency/performance audit. No backend restart or frontend build was performed.
Legacy risks and future-worker prerequisites documented above still apply.

Final local suite: `venv\\Scripts\\python.exe -m pytest tests -q` — **198 passed**,
four preexisting warnings. This includes the new database-name regression test.
