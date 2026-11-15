# Dashboard restructuring: reviewable increments

This is an incremental migration, not a dashboard redesign. No bulk file moves.

## Inspection findings

- `views/dashboard/Dashboard.jsx` already shares Sidebar, theme initialization and Outlet; reuse it.
- `components/ui/Sidebar.jsx` hardcodes navigation. Its hover/focus and mobile controls must remain intact.
- `router/index.jsx` has a reusable AuthBoundary with allowedRoles support, but no `/admin` branch yet.
- `components/Layout.jsx` recognizes `/dashboard` only; add `/admin` when introducing platform routes.
- SystemHealth currently exposes platform-oriented demo information to all dashboard roles. Restrict the page and any relevant backend endpoints together in step 2.
- Overview, AttackInsights, DefenseMetrics, ScanResults, ActivityLogs and SystemHealth contain local demo data; dashboardStore also contains independent static values. Reconcile rather than blindly deleting either source.
- AttackInsights and ScanResults duplicate vulnerability/patch concepts; DefenseMetrics overlaps remediation.
- Card, Widget and Table already exist; prefer those patterns before introducing additional abstractions.
- `pages/dashboard/index.js` re-exports the existing views. Preserve compatibility until consumers are checked.

## Step 1 — navigation extraction (implemented)

Added `src/dashboard/navigation/navigation.js` and focused compatibility tests.
Sidebar consumes that configuration using the authenticated role. Existing labels,
order, destinations, icons, CSS and interaction handlers are unchanged. There are
no new/deleted routes or renamed/moved pages. This step is NOT the platform access
restriction: all three existing roles retain their original navigation.

## Subsequent review boundaries

### Step 2 — Platform Health access boundary (implemented)

- Added `/admin/platform-health` and `/admin/settings` under the same Dashboard
  layout, behind the existing AuthBoundary restricted to superadmin.
- `/admin` currently lands on Platform Health, the first implemented platform
  screen. No fake platform overview or management screens were introduced.
- Login without a requested return URL and authenticated guest-page redirects
  now use a centralized role landing helper. Existing customer redirects remain.
- Customer navigation no longer includes System Health. Superadmin additionally
  sees the two implemented platform destinations; workspace links remain available.
- The legacy `/dashboard/system-health` URL checks the superadmin role before
  redirecting to the new destination. Customers return to their overview.
- `/api/dashboard/system-health` now independently requires superadmin.
- Reused SystemHealth in place (no file move), renamed its displayed title to
  Platform Health, and explicitly marked simulated metrics/logs as demo data.
- Outer Layout now recognizes the `/admin` namespace, avoiding public header/footer.
- No other page styling, data contracts, settings behavior, or website routes changed.

Backend must be restarted to load its changed authorization dependency if running
without reload. Automated checks cover navigation policy and backend role dependencies;
interactive desktop/mobile and complete browser route-matrix checks remain pending.

1. **Platform access boundary:** introduce a superadmin-only `/admin` branch using the existing layout; update outer chrome and role landing redirects; move SystemHealth to Platform Health. Guard the old direct URL too. Test customer denial and superadmin access before enabling platform navigation. Do not create fake organizations/users/agents screens.
2. **Customer terminology and responsibilities:** repurpose AttackInsights as Findings, DefenseMetrics as Remediation, ActivityLogs as Activity. Keep compatibility redirects. Replace simulated patch execution with honest draft/review actions, not just renamed buttons.
3. **Shared demo domain data:** centralize projects/assets/runs/findings/remediation/activity relationships and statuses. Convert Overview metrics/charts using the existing visual components; clearly mark demo values.
4. **Projects and Assets:** add lists and project detail tabs; reuse shared page bodies scoped by project. Move reconnaissance into Assets or run details. No backend project engine.
5. **Security Runs:** introduce list/detail routes; reuse ScanResults and ArchitectureMap where appropriate. Keep simulated progress distinguishable from live execution.
6. **Settings and cleanup:** extract only reusable settings sections; verify compatibility imports before removing old files. Validate role navigation, direct URLs, refresh, back/forward, logout and desktop/tablet/mobile behavior.

## Intended navigation (not all implemented yet)

### Step 12 — browser verification (in progress)

- Admin browser pass: confirmed Demo Admin identity and no Platform menu. Direct
  /admin/platform-health, /admin/settings and /dashboard/system-health all redirect
  to /dashboard/overview. Refresh preserves the admin session.
- Empty Public API project shows no assets, findings, remediation, activity or runs;
  populated project records do not leak into these empty project views.
- Finding details and remediation draft preview open; read-only remediation review
  expands. No actual draft submission, approval, scanning or patching was performed.
- Activity unmatched search shows an empty result; Project created event filter
  exercised and restored. No captured browser errors. Admin remains signed in.
- Rechecked event filtering from a fresh Activity view: Project created returns
  only DEMO-ACTIVITY-8. Initial combined search-clear/filter check was inconclusive.
- User-role browser pass remains pending; backend role enforcement is not established
  by these client-side redirects. No build or application code changes in this pass.
- Follow-up interaction pass: light theme and email preference survived refresh;
  disabling email disabled critical alerts. Save confirmation appeared. Restored
  original dark theme and email preference through the UI afterward.
- Removed misleading Settings LIVE TELEMETRY pseudo-label; verified absent in DOM.
  Lint passed; no build run.
- Opened populated project, scoped asset and completed-run details; reconnaissance
  and associated findings render. Run creation remains disabled as intended.
- Sign out redirects to login; direct Platform Health access and subsequent refresh
  remain at login. Left browser signed out for customer-role verification.
- Still pending: admin/user access denial checks and broader empty-state/filter/
  finding/remediation interactions. This is not a declaration of complete browser QA.
- Authenticated superadmin browser pass: Platform Health survives refresh; all ten
  sidebar destinations finish rendering. Settings/Platform Settings back/forward
  navigation works, and /auth/login redirects back to Platform Health while signed in.
- Desktop sidebar returns to 82px after mouse selection and pointer exit. Keyboard
  navigation opens each destination. Phone menu aria-expanded changes true to false
  after selecting Overview.
- At 390px, Overview, Projects, Assets, Findings, Security Runs, Remediation, Activity
  and Settings have no document horizontal overflow. Platform Health and Settings
  phone screenshots were inspected. At 768px all ten sidebar pages have no document
  horizontal overflow. No captured browser errors during this pass.
- Restored the viewport override and retained the signed-in session. Customer-role
  denial, logout, preference mutations/theme switching and nested detail interactions
  are still unverified in-browser; these checks are not implied by the navigation pass.
- Login connection follow-up: backend responds on loopback, but not the frontend's
  LAN hostname on port 8000. Added Vite /api proxy to 127.0.0.1:8000 and same-origin
  development API default; explicit VITE_API_URL and production defaults remain.
- Verified POST /api/auth/login through 192.168.159.1:3000 with an empty payload
  returns the backend's HTTP 400 validation response, not connection refused.
  This confirms transport only; successful credential/session verification is pending.
- Added API connection/error tests; all 40 tests and lint pass. No build run.
- Confirmed the existing frontend is reachable at 192.168.159.1:3000 and backend
  OpenAPI responds with HTTP 200 at 127.0.0.1:8000 (not a database/login health test).
- In a fresh in-app browser, unsigned-in /dashboard/overview redirects to login
  with its return URL. /login redirects to /auth/login.
- No existing authenticated browser session is available. Authenticated navigation,
  refresh, role denial, logout and dashboard responsive checks await user sign-in.
- The extra frontend instance started for diagnosis was stopped; existing servers
  were left untouched. No production build or application-code changes in this step.

### Step 11 — Settings extraction and cleanup audit (implemented)

- Extracted Account, Appearance and Toggle components without changing their CSS
  classes or layout. Kept the existing Settings entry point and compatibility exports.
- Platform Settings now has explicit platform context while reusing personal settings;
  it does not claim to configure platform-wide services. Existing role guards remain.
- Extracted browser preference persistence with boolean validation, legacy-key
  compatibility, corrupt-storage defaults and visible save/reset failure messages.
- Clarified that notification and compact-table preferences are local previews, not
  connected services. Theme remains immediate and separate from preference reset.
- Reference audit found ScanResults still exported by pages/dashboard/index.js;
  retained legacy files rather than breaking compatibility with an unverified removal.
- 38 tests and lint passed. No build run. Browser layout, route/session and responsive
  verification remain the next increment; no backend services were changed.

### Step 10 — grouped navigation (implemented)

- Grouped customer links into Workspace, Security, Operations and Management.
- Superadmin additionally sees Platform, containing only the implemented Platform
  Health and Platform Settings pages. No placeholder management pages were added.
- Centralized section ordering and role filtering; empty sections are omitted.
- Preserved existing sidebar icons, styling, hover/focus behavior and mobile close
  handlers. Added mobile toggle accessibility attributes.
- Allowed the navigation area to scroll while keeping sidebar header/footer from
  shrinking, accommodating the longer grouped menu on shorter screens.
- No routes, authorization guards or backend behavior changed; no files renamed.
- All 34 tests and lint passed. No build run; frontend/dist remains absent.
- Browser verification of hover, keyboard and mobile interactions remains pending.
- Next increment: Settings extraction and reference-checked cleanup, followed by
  browser route/session/responsive verification.

### Step 9 — Overview slice (implemented)

- Reused Overview.jsx, Widget/Card, Chart.js and existing overview layout classes.
- Replaced SIEM metrics with Security Score (not assessed), Open Findings, Critical
  Findings and the latest started Security Run. Queued fixtures are not counted as started.
- Added a pure overview selector using shared findings, runs, remediation and activity.
- Charts now show cumulative discovery by fixture dates and open-finding severity,
  rather than invented threat numbers. Discovery history is not misrepresented as
  historical open-finding counts. Theme changes refresh chart colors and cleanup destroys instances.
- Added critical/recent findings, recent run links, unresolved demo proposal count and
  recent activity. No per-page fabricated timestamps or fake live-telemetry label remain.
- Removed Overview's dependency on legacy monitoring/content stores, but did not delete
  those stores because other pages may still consume them. No backend changes.
- Added selector tests for fixture consistency, resolved findings, empty/queued cases,
  and non-mutating activity ordering. 31 tests and lint passed. No build run.
- Responsive widget wrapping retained within existing cards; browser/chart rendering
  and mobile verification remain pending the dedicated verification increment.

### Step 8 — Security Runs slice (implemented)

- Added shared demo run records, lifecycle labels, scoped lookup and finding selectors.
- Added `/dashboard/security-runs` and `/dashboard/security-runs/:runId`, plus
  equivalent project-scoped list/detail routes. All inherit the dashboard guard.
- Enabled Security Runs in sidebar/project tabs and project overview counts.
- Reused Card and Reconnaissance visual components. Run details show asset context,
  status/dates/progress, scoped findings, illustrative timeline and an honest logs empty state.
- Queued demo has no start/completion date, findings, or fabricated execution logs.
- New Security Run is disabled with an explanation; no engine or queue added.
- `/dashboard/scan-results` redirects to the run list. Its old component remains on
  disk for later cleanup, avoiding reuse of its simulated patch/execution semantics.
- Overview no longer opens SecurityScanner; it links to Security Runs instead.
- ArchitectureMap remains unchanged and is not linked to unrelated demo runs. Further
  project/run-specific architecture integration and browser verification remain pending.
- Added tests for run/asset/finding integrity, lifecycle labels, bounds and empty/wrong-project cases.
- No backend changes or build. Lint passed; focused unit checks run alongside existing tests.

### Step 7 — Assets slice (implemented)

- Added Assets list/detail and reusable Reconnaissance components under dashboard/assets,
  plus shared demo inventory, asset-type labels, project-aware lookup and relationship tests.
- Routes: `/dashboard/assets`, `/dashboard/assets/:assetId`, and equivalent nested
  `/dashboard/projects/:projectId/assets` and `/dashboard/projects/:projectId/assets/:assetId` routes.
- Enabled project Assets tab and asset counts; added Assets to the existing sidebar.
- Reused Card, recon-card and responsive grid styling. No pages moved/renamed.
- Findings now reference stable asset IDs; their details use the same reconnaissance
  component and demo observations as asset details. Removed duplicated recon state/markup.
- Unknown/wrong-project assets return not-found; projects without assets stay empty.
  A demo repository explicitly has no reconnaissance rather than fabricated results.
- No backend inventory, scanning or tenant authorization changes. Fixtures are demo-only.
- Validation: focused relationship tests and lint. Browser/mobile checks remain pending.
- No build run; preserve the user's no-build instruction.

### Step 6 — Projects slice (implemented)

- Added `dashboard/projects/Projects.jsx` (list, shared project layout and overview),
  `demoProjects.js`, and relationship tests. No existing pages moved or renamed.
- Routes: `/dashboard/projects`, `/dashboard/projects/:projectId` (overview redirect),
  and nested `overview`, `findings`, `remediation`, `activity`. All inherit dashboard auth.
- Project tabs reuse the existing Findings/Remediation/Activity pages filtered by a
  stable `projectId`. No duplicate role-specific pages or backend projects added.
- Two explicit demo projects include an empty-project case. Unknown IDs render a
  not-found state. Global activity without a project is excluded from project views.
- Shared project identity is used by findings, remediation and workspace activity
  fixtures. UI fixture filtering is NOT a replacement for future backend tenant checks.
- Added Projects to the sidebar. Existing Card styles, dark/light variables and
  auto-fitting grids are reused. Tabs wrap; Assets/Security Runs are non-link future labels.
- Tests: 20 passed. Lint passed. Browser navigation/responsive checks remain pending.
- No build run, per the updated user instruction. Future builds require explicit approval.

### Step 5 — Activity slice (implemented)

- Reused ActivityLogs.jsx and its responsive table/filter classes without moving it.
- Added `/dashboard/activity`, redirecting `/dashboard/activity-logs`; updated sidebar
  and Overview's activity link. Platform audit-log routes are not introduced here.
- Centralized demo events and event labels under `dashboard/activity`. Preserved all
  eight historical security examples alongside illustrative workspace lifecycle events.
- Added type filtering and broader null-safe, case-insensitive search for event ID,
  description, type, project, actor, IP and status; newest events sort first.
- Updated table context to accommodate non-IP events and exposed pressed filter state
  and accessible search/select labels. Existing horizontal table overflow is retained.
- Removed this page's live-telemetry label and stale content-store title overrides.
- Examples are not a live audit trail or records of the demo actions taken elsewhere.
- Added tests for event coverage, legacy preservation, combined filters, empty data,
  optional fields and stable non-mutating sorting. Browser/mobile checks remain pending.

### Step 4 — Remediation slice (implemented)

- Reused DefenseMetrics.jsx in place, including its summary card SVGs, CSS classes
  and proposal-card patterns. No page files were renamed or moved.
- Added `/dashboard/remediation`; `/dashboard/defense-metrics` redirects there.
- Sidebar uses Remediation with the existing icon. All customer routes remain protected.
- Removed this page's threat-feed/compliance/patch-success fixtures and nonfunctional
  Apply Fix / Apply Now / Rollback actions. Other screens are unchanged.
- Added centralized remediation statuses and fixtures derived from existing demo
  finding IDs, project and asset context. Summary counts are calculated, not invented.
- Read-only Review Remediation disclosures show proposed changes and validation
  requirements, without mutations, fake execution, or approvals.
- Clearly states these examples are not the page-session drafts created in Findings.
  Shared draft persistence, real remediation APIs, approval rules and execution remain future work.
- Added tests for finding relationships, lifecycle labels, derived counts and empty data.
- Browser/mobile interaction checks remain pending; existing responsive CSS is reused.

### Step 3 — Findings slice (implemented)

- Reused `views/dashboard/AttackInsights.jsx` in place: no file rename and no CSS redesign.
- Added `/dashboard/findings`; `/dashboard/attack-insights` now redirects there.
- Sidebar points to Findings with the existing icon and active-link behavior.
- Extracted fixtures into `dashboard/findings/demoFindings.js` and lifecycle constants
  into `status.js`; added fixture-contract tests. Demo identifiers do not claim verified CVEs.
- Cards retain severity/CVSS and now show project, asset, source run, finding status
  and remediation-draft state. Fixture contracts include category and detection dates.
- Removed timed patch execution, fake successful-fix claims, writes to the patch store,
  and deletion of supposedly patched findings. Create Remediation now opens a demo
  proposal; creating it only records a page-session draft and leaves the finding open.
- Reconnaissance moved out of the global list into finding details, marked as demo
  source-run context. Further reuse in Assets/run details is pending those pages.
- DefenseMetrics/ScanResults actions and the remainder of the roadmap are unchanged.
- Validation: 10 frontend unit tests and lint passed; browser interaction and responsive
  checks are still pending. Drafts intentionally do not persist across refresh/navigation.

Customer: Workspace / Overview; Security / Projects, Assets, Findings, Security Runs,
Remediation; Operations / Activity; Management / Settings.

Platform: Platform Overview, Organizations, Users, Security Runs, Agents, Platform
Health, Audit Logs, Settings. Only link implemented destinations.

## Validation policy

Each increment gets focused tests and lint. Per the updated user instruction, do
not run builds unless explicitly requested; keep generated dist absent.
Browser verification is required for later visual/route changes. Step 1 only tests
configuration compatibility; it does not claim the final role/route matrix is complete.
