# HavoSec Single-Agent Remediation Loop V1

This milestone extends the completed repository discovery cycle. It does not replace
the scanner, normalizer, worker, authorization, persistence, or existing single agent.
HavoSec V1 does not modify customer repositories automatically.

## Step 1 — live Projects migration

- Replaced the Projects list's demo records with the organization-scoped Projects API.
- Project cards now show only real project fields: name, description, status, and
  creation date. Missing values are stated plainly rather than fabricated.
- Project layout now loads and validates the selected project through the backend.
- Project overview uses the real scoped overview aggregation for asset, run, finding,
  remediation, and recent-activity information.
- Existing links continue to connect project Assets, Security Runs, Findings,
  Remediation, and Activity through their domain relationships.
- Preserved the existing dashboard design and authorization behavior.

Focused verification: ESLint passed for the changed files; 2 test files and 5 tests
passed. No frontend production build was run during this incremental step.

Next: migrate the top-level Overview and Activity pages from demo data to their existing
real domain APIs, then migrate Remediation before adding validation and patch execution.

## Step 2 — live Overview and Activity

- Replaced the top-level Overview demo aggregation with `/api/domain/overview`. Open and
  critical finding counts, severity distribution, latest/recent security runs, recent
  findings, remediation count and recent activity are now organization-scoped backend
  values.
- Security Score and historical assessment coverage remain explicitly unavailable; the
  UI does not derive or imply either from incomplete data.
- Replaced the Activity demo table with `/api/activity`, including optional project
  scoping, real lifecycle event labels, client-side text/type filtering, loading/error
  states and a truthful empty state. Removed severity/status columns because the domain
  event model does not provide those values.
- Extended the shared API adapter and activity presentation adapter rather than adding
  component-specific HTTP calls. Existing visual components and layout were preserved.

Focused verification: ESLint passed and **4 test files / 13 tests passed**. No frontend
build ran. Next: migrate the Remediation page to the real domain API and review the
existing remediation model/lifecycle before extending it.

## Step 3 — live Remediation page

- Replaced demo remediation records with organization-scoped `/api/remediations` data
  and related real Findings. Optional project routes pass the existing project filter to
  both endpoints.
- The summary cards now cover every status supported by the current backend lifecycle:
  pending, in progress, awaiting approval, approved, rejected and resolved.
- Review cards show the stored summary, recommendation, proposed fix, source Finding,
  severity, project and timestamps. Missing data is labelled unavailable rather than
  fabricated.
- The page clearly states that these existing records are human-managed proposals and
  have not yet passed the new isolated patch-validation and scanner-verification loop.
  It exposes no execution or status-changing action yet, avoiding a false claim that an
  old approved record was technically verified.
- Extended the shared API adapter with Finding detail and Remediation list/detail methods.
  Backend organization isolation and authorization remain authoritative.

Focused verification: ESLint passed and **3 test files / 8 tests passed**. No frontend
build ran. The remaining deferred customer dashboard pages are now connected to domain
APIs. Next: formalize structured Finding validation in the backend before allowing new
automated remediation proposals.

## Step 4 — structured deterministic Finding validation

- Added an embedded, typed `ValidationResult` to the existing Finding contract instead
  of creating a duplicate Finding or validation collection. It records the source run,
  allowed status, bounded confidence and summaries, supporting factors, uncertainties,
  method, requesting actor and timestamp. It never stores chain-of-thought.
- Added `POST /api/findings/{finding_id}/validate` for admins/superadmins. Existing
  organization, project, asset and run relationship checks execute before validation;
  users remain read-only and cross-organization records continue returning no access.
- The first validator is deterministic and executes no repository code, exploits or
  network requests. Complete Semgrep rule/location/source-hash evidence plus commit and
  fingerprint produces `likely`, explicitly noting that exploitability was not proven.
  Incomplete evidence produces `needs_review`. It never promotes a Finding to confirmed
  or resolved by itself.
- Validation persistence and a single `finding_validated` activity event are committed
  together using the existing optimistic/transactional repository path. Activity stores
  only status, method and confidence metadata.
- `confirmed` and `rejected` are valid structured outcomes reserved for the later
  agent-assisted/human assessment path. Automated remediation eligibility has not yet
  been enabled.

Focused verification: **35 backend tests passed**, covering likely/needs-review results,
stored output, unchanged Finding state, activity, user denial, tenant isolation,
authentication and transactional rollback. No external AI call, scanner execution,
frontend build or production data mutation occurred.

Next: extend the existing single analysis agent with a strictly structured validation
assessment and deterministic fallback/decision policy, then enforce remediation
eligibility from the stored validation result.

## Step 5 — single-agent validation and remediation eligibility

- Extended the existing `FindingAnalysisAgent`; no second agent or orchestrator was
  introduced. Its new validation operation accepts bounded Finding/scanner/prior-analysis
  data marked explicitly as untrusted and returns a strict `ValidationAssessment` schema.
  It has no tools and cannot execute code, exploits, commands or network target checks.
- Provider failure, timeout or malformed output returns no assessment and preserves the
  deterministic ValidationResult. Automated tests use a fake provider; no paid/external
  AI request was made.
- Added an application-owned decision policy. An agent recommendation cannot directly
  control state: `confirmed` requires complete deterministic evidence plus an agent
  confidence of at least 0.85; a high-confidence rejection requires at least 0.90;
  ambiguous combinations become `likely` or `needs_review` conservatively.
- Enforced remediation eligibility in `RemediationService`. Findings without stored
  validation, or validated as `needs_review`/`rejected`, are rejected. `confirmed`
  findings are eligible; `likely` findings require an explicit human-review
  acknowledgement in the create request. That acknowledgement is a control input and is
  not persisted as if it were evidence.
- Existing tenant/project relationship validation and admin authorization execute before
  remediation creation. No patch is generated or applied in this step.

Focused verification: **46 backend tests passed**, covering valid, unavailable and
malformed agent responses, conservative decision thresholds, remediation eligibility,
explicit likely acknowledgement, role enforcement, organization isolation and rollback.
No external AI call, source modification, scanner run, frontend build or production data
mutation occurred.

Next: extend the Remediation contract with a strictly structured proposal and unified-diff
artifact, then implement path/size/file-count/symlink safety validation before any patch
can enter an isolated workspace.

## Step 6 — structured remediation proposal and patch safety boundary

- Added strict `RemediationProposal` output for the same single HavoSec agent: summary,
  explanation, unique affected files, unified diff, expected security effect, bounded
  side effects/tests and confidence. Extra/malformed output falls back to no proposal;
  HavoSec never fabricates a patch when the provider is unavailable.
- Remediation records now preserve the source Asset, SecurityRun and commit where
  available, the validation status used for eligibility, an optional structured proposal,
  patch format and a distinct verification status. Existing manual records remain
  readable through optional/default fields.
- Added centralized remediation controls: total timeout, patch byte/file limits, a V1
  attempt limit of one (bounded to at most two), workspace size limit and agent request
  timeout. Environment parsing rejects out-of-range values.
- Added a deterministic unified-diff safety validator. It permits only modifications to
  declared, unique, existing repository-relative text files. It rejects absolute paths,
  traversal, `/dev/null` create/delete operations, renames, backslashes, malformed or
  binary patches, undeclared files, duplicates, excessive bytes/files, missing files and
  any symbolic-link path component. Canonical resolution must remain inside the checkout.
- The proposal prompt continues treating all repository/finding content as untrusted data
  and prohibits commands, repository writes, commits, pushes, pull requests, deployments
  and unrelated changes. Recommended tests are review text only and are never executed.
- This step validates artifacts only. It does not apply a patch or modify any checkout.

Focused verification: **98 backend tests passed**, covering proposal schema/fallback,
valid patches, absolute/traversal/new-file rejection, symlink rejection, size/file-count
limits, malformed patches, declared-file mismatches, configuration and existing domain
regressions. No external AI call, patch application, scanner run, frontend build or
production data mutation occurred.

Next: implement a dedicated remediation workspace that checks out the Finding's exact
source commit, creates separate original/patched trees, applies only a `SafePatch`, and
guarantees cleanup without executing repository-provided code.

## Step 7 — exact-commit isolated remediation workspace

- Added an exact-revision Git checkout path for remediation. It initializes a fresh
  checkout, fetches only the Finding's lowercase 40-character source commit with
  interactive credentials disabled, detaches at that revision and verifies that `HEAD`
  exactly matches before continuing. Invalid, unavailable or mismatched revisions fail
  closed.
- Added a dedicated per-attempt remediation workspace with separate immutable-source and
  patched trees plus an artifacts directory. The patched tree is created as an isolated
  copy, and the configured workspace limit accounts for both copies rather than either
  one independently.
- Added deterministic `SafePatch` application using argument-array Git commands. The
  patch must pass the Step 6 validator first, then `git apply --check`, before it can be
  applied to the patched tree. The original tree is never the patch target.
- Cleanup is unconditional on both normal completion and exceptions, including Windows
  read-only Git files. Preservation remains possible only through an explicit internal
  `keep` option; no API currently exposes it.
- This boundary runs no repository-provided programs, package managers, hooks, test
  commands, exploits or deployments. It performs only source checkout, bounded copying,
  deterministic patch validation/application and artifact capture.

Focused verification: **30 backend tests passed**, covering exact-commit checkout and
verification, invalid/mismatched revision rejection, original/patched isolation,
combined workspace limits, successful patching, unsafe pre-execution rejection,
controlled patch-check failure and cleanup on success/error. No external AI call,
scanner run, frontend build or production data mutation occurred.

Next: connect this boundary to the remediation worker lifecycle, run the permitted
Semgrep verification in the patched tree, persist before/after evidence and ensure every
outcome reaches a terminal review state without running repository-provided commands.

## Step 8 — worker verification and deterministic before/after policy

- Extended the existing security worker framework to claim both discovery runs and
  remediation-verification work. Remediation claims are atomic, carry the same worker
  ownership/lease pattern and emit one meaningful verification-started activity event.
  No second autonomous agent or unrelated worker framework was introduced.
- Added a structured `VerificationResult` with the original-finding presence flag,
  before/after finding and severity counts, new-finding counts, scanner identity/version,
  concise summary and timestamp. Scanner failure remains distinct as `inconclusive`.
- The worker reloads and revalidates the Project, Asset, Finding, stored proposal,
  original scanner evidence, repository authorization and exact source commit after it
  claims the job. Missing, cross-related or stale source data fails closed.
- Verification checks out the exact Finding revision into the isolated original tree,
  copies it to the patched tree, validates/applies the patch there, and runs only the
  allowlisted Semgrep adapter against the patched tree. Repository-provided commands,
  tests, hooks and agent-suggested commands remain prohibited.
- Implemented the V1 comparison policy: a proposal is `verified` only when the original
  rule/path/line finding disappears and the patch introduces no new finding at equal or
  higher severity. A remaining target or qualifying regression is `failed`; scanner,
  checkout or timeout uncertainty is `inconclusive`.
- The after-patch Semgrep result is stored as a separate raw scanner artifact and never
  overwrites the discovery evidence. Result persistence, remediation state and the final
  verified/failed activity event are transactional. A verified proposal becomes
  `awaiting_approval`; the original Finding is deliberately not marked resolved.
- Expired remediation claims are recovered to an explicit inconclusive/failed review
  state. Workspace cleanup remains unconditional for successful and failed scans.

Focused verification: **97 backend tests passed**, including target disappearance,
target persistence, new equal-severity regression, scanner failure, workspace cleanup,
atomic remediation claiming, transactional result/evidence persistence, existing worker
behavior, patch safety and domain/RBAC regressions. The updated worker also passed a
direct import check. No external AI call, repository-provided command, frontend build or
production data mutation occurred.

Next: add the authorized API operation that freezes/generates a structured proposal and
atomically queues one verification attempt, including stale-state and duplicate-claim
guards. Then expose that lifecycle through the existing Remediation dashboard.

## Step 9 — authorized verification queue and worker proposal handoff

- Added `POST /api/remediations/{remediation_id}/verify` for existing admin/superadmin
  project-management authority. The request performs relationship, active-project,
  eligible-validation, reproducible-source, current-state and configured-attempt-limit
  checks, then atomically records a queued attempt and returns `202`.
- Duplicate requests cannot queue an already queued, testing or verified remediation.
  Attempt counts are persisted and bounded by `MAX_REMEDIATION_ATTEMPTS`; user-role and
  cross-organization enforcement continues through the existing backend dependencies and
  tenant-scoped repository update.
- The API executes no checkout, model request, patch or scanner. Those operations remain
  entirely asynchronous in the existing worker and under its lease/ownership controls.
- When a remediation has no frozen proposal, the worker checks out the exact source
  commit first, extracts only a bounded window around the Finding's repository-relative
  source location with traversal/symlink containment checks, and calls the same configured
  `FindingAnalysisAgent.propose_remediation()` operation. It does not send the repository.
- A valid structured proposal is stored with unified-diff format and aggregate,
  non-sensitive usage metadata before application. Invalid/malformed/provider-unavailable
  output produces an explicit failed result; HavoSec never fabricates a fallback patch.
  Existing proposals are reused rather than regenerated during verification.
- Added distinct `remediation_verification_queued` audit events and response fields for
  attempt count, proposal metadata and the structured verification result.

Focused verification: **82 backend tests passed** for the queue authorization/state
boundary, bounded single-attempt behavior, same-agent proposal generation and freezing,
line-accurate source context, unavailable-agent failure, worker verification, activity
events and existing domain/RBAC behavior. No external AI request, frontend build,
repository-provided command or production data mutation occurred.

Next: expose proposal, diff, verification evidence and authorized Verify/Approve/Reject
actions in the existing Remediation dashboard, with polling only while verification is
queued or testing.

## Step 10 — live remediation review and approval UI

- Connected the existing Remediation dashboard to the asynchronous verification action
  and existing lifecycle update API. Admins/superadmins can request Generate & Verify or
  Verify Fix, approve only scanner-verified proposals awaiting approval, and reject
  pending/approval-ready proposals. Normal users retain read-only review access; backend
  RBAC remains authoritative.
- Polling now runs only while at least one visible remediation is `queued` or `testing`
  and stops at every terminal state. Action errors remain attached to the relevant record
  and backend conflict messages are shown without optimistic status fabrication.
- Expanded review details now present the source Finding, severity, validation status,
  repository-relative location/rule, source commit, structured proposal explanation,
  affected files, expected effect, confidence, side effects and recommended human tests.
- Added a readable, horizontally bounded unified-diff view with distinct header, hunk,
  addition and deletion styling. Temporary workspace paths are never exposed.
- Added the structured verification summary: original-finding presence, before/after
  totals, all new findings, equal-or-higher regressions, scanner/version and timestamp.
  The UI explicitly states that verified means only the isolated copy passed the policy;
  HavoSec has not changed a customer repository or resolved the original Finding.
- Added labels for queued/started/verified/failed remediation activity and all verification
  statuses, including the internal failed remediation state.

Focused verification: ESLint passed for every changed frontend module, and **2 frontend
test files / 8 tests passed** for remediation contracts/diff rendering and activity
presentation. No production build was run during this incremental step.

Next: add the deterministic HavoSec-owned vulnerable fixture and known-good patch, then
execute the complete scanner → patch → rescan comparison loop without AI or customer
repository access.

## Step 11 — deterministic known-good remediation proof

- Added a 283-byte known-good unified diff beside the existing HavoSec-owned vulnerable
  fixture. It replaces Python `eval` with `ast.literal_eval`; the fixture and patch remain
  test-only and no fixture code is imported or executed.
- Added a real integration proof that creates an immutable local Git commit, runs the
  production Semgrep adapter, checks out that exact commit through the remediation Git
  adapter, creates separate original/patched trees, validates and applies the known-good
  patch, runs Semgrep again and applies the production before/after comparison policy.
- The real Semgrep 1.176.0 scan produced two findings before the patch and one afterward.
  The targeted `havosec.python.eval` finding disappeared; the unrelated existing
  subprocess finding remained; zero new findings and zero equal-or-higher regressions
  were recorded; the verification result was `verified`.
- The proof asserts the source repository and immutable original checkout remain byte-for-
  byte unchanged, only the patched copy contains `ast.literal_eval`, and the remediation
  workspace no longer exists after the context exits.
- The first real run exposed a comparison edge case: adding an import shifted the line of
  an unrelated existing finding. Regression matching now uses per-rule/per-file occurrence
  counts so a line shift is not mislabeled as a new issue, while the original target still
  requires exact rule/file/line disappearance. A dedicated regression test preserves this
  behavior.

Verification: the real deterministic Semgrep proof passed, then the broader focused
security-engine suite passed **65 tests**. No AI request, customer repository access,
repository-provided command, frontend build or production database mutation occurred.

Next: run the full backend and frontend verification suites, perform the required
production frontend build once, remove generated build output afterward if required by
the workspace policy, and complete the final documentation/report. A database-backed
API/worker demonstration can then be performed if the configured local services and
credentials are available.

## Step 12 — complete automated acceptance verification

- The complete backend suite passed **330 tests** in 30.17 seconds. This includes domain,
  authentication/RBAC, tenant isolation, worker leases/cancellation, discovery,
  validation, agent schema/fallback, patch safety, isolated remediation, before/after
  comparison, API queueing and the real Semgrep fixture proof.
- The complete frontend suite passed **12 test files / 43 tests**. Full ESLint verification
  also passed without suppressions or automatic rewriting.
- The required Vite production build completed successfully after transforming 822
  modules. It reported only a non-blocking advisory that the separately emitted Three.js
  module is larger than 500 kB; this is a performance optimization opportunity, not a
  compilation failure.
- Per the workspace requirement, the generated `frontend/dist` directory was removed
  after the successful build and its absence was verified (`dist_exists=False`).
- A credential-safe read-only ping confirmed that the configured MongoDB service is
  reachable. No production/database records were mutated during this verification step.
- Existing dependency warnings remain visible: Starlette's legacy multipart import,
  class-based/removed-key Pydantic configuration in older architecture routes, one
  `datetime.utcnow()` use in platform health, and stale Browserslist metadata. None was
  suppressed, and none failed the acceptance suite.

Automated acceptance status: **passed**. The milestone is not yet being declared fully
complete because the required disposable database-backed API/worker demonstration and
captured lifecycle IDs have not been executed. That is the final remaining step; it must
create only clearly test-owned records, exercise queue → worker → persisted verification
→ approval-ready state, report the required fields, and clean those records afterward.
