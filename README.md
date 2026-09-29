# RecruitIQ — Full Stack (Backend Sprints 1-5, Frontend Foundation + Sprints 4-5)

## Milestone 1 achieved — the full MVP loop works

Backend Sprints 1-3 (auth, tenant/RBAC, departments/teams, company settings,
jobs with a full approval workflow) plus two real gap-fixes found during
review (see below), Sprint 4 (candidates/resumes/storage), and Sprint 5
(applications + public career portal — the milestone-closing sprint) are all
implemented, backend and frontend together, feature by feature.

## Gap-fixes found and corrected during this build (not carried forward silently)

1. **`api/v1/companies/` never existed** despite being in the original folder
   plan — departments/teams got built under `api/v1/org/` instead, and
   company-level settings had no endpoint at all. Fixed: `GET/PATCH
   /api/v1/companies/me` with a proper `company.manage_settings` permission
   (not a mismatched reuse of `admin.manage_users`).
2. **Pipeline template CRUD (`API-3`) was never built in Sprint 3** — only Job
   CRUD was. Fixed at the start of Sprint 5, since Applications can't function
   without a pipeline to move candidates through.
3. **`JobSchema` was missing `pipeline_template_id`** in its output — caught
   during an explicit frontend/backend field-name cross-check before shipping,
   not after.

## Sprint-by-sprint summary

**Sprint 1 — Auth foundation:** Company/Role/Permission/User models, JWT
login/refresh (with rotation + reuse detection)/logout/logout-all, the
tenant-scoped repository pattern that makes cross-tenant queries structurally
impossible, not just discouraged.

**Sprint 2 — Tenant scoping, RBAC, departments:** Department/Team CRUD,
`@require_permission` wiring, the cross-tenant-404 test (proves a Tenant A
actor never sees Tenant B data, not even a 403 that would confirm existence).

**Sprint 3 — Jobs & pipelines:** Job status state machine
(`draft→pending_approval→published→closed→archived`) as an independently
unit-tested validator, approval-step routing that auto-publishes once all
steps approve.

**Sprint 4 — Candidates, resumes, storage:** `Candidate` (global identity) /
`CandidateProfile` (tenant-scoped) split, resume upload with **real
magic-byte validation** (rejects a renamed executable even when named
`resume.pdf`), `LocalStorage` returning signed/expiring URLs to mirror S3's
security contract in dev.

**Sprint 5 — Applications & public portal (Milestone 1 exit criteria):**
`Application`/`ApplicationStageHistory` (append-only) models, the public
unauthenticated career portal (browse → job detail → apply, with tighter
rate limits than authenticated routes), and **the full E2E test**: pipeline
created → job created → submitted → approved (auto-publishes) → candidate
applies via the *public* portal with zero auth → recruiter moves the stage →
timeline shows both entries in order.

## Frontend (new this batch — none existed before)

Vite + React + Tailwind + TanStack Query + React Router, with a deliberate
design system (ink/signal color tokens, Fraunces+Inter type pairing) rather
than default styling. Built:
- **Auth**: login page, in-memory access token + HttpOnly refresh cookie,
  automatic 401→refresh→retry interceptor, silent session restore on reload
- **Candidates**: list, add-candidate form, per-row resume upload
- **Jobs**: list, create (with pipeline template selection), kanban-style
  pipeline board with move-to-next-stage actions, submit-for-approval
- **Public career portal** (separate from the authenticated shell entirely):
  job listing, job detail + apply form with resume upload and a real success state

## Verification discipline maintained throughout

Every model cross-checked column-by-column against its migration. Every
seed-permission reference checked against `SYSTEM_PERMISSIONS` (zero drift).
The app genuinely boots and lists all 41 routes. 13 unit tests genuinely
executed — not just syntax-checked — covering the state machine and file
upload validation. The frontend genuinely `npm install`'d and `npm run
build`'d (154 modules, zero errors). Field-name consistency was explicitly
cross-checked between backend schemas and frontend consumers, which is what
caught gap-fix #3 above before shipping rather than after.

## Known gaps, stated plainly

- ~~Integration tests (including the Milestone 1 E2E test) have not executed
  against a live Postgres anywhere in this build~~ **Resolved in Sprint 13**:
  the full suite (199 tests as of Sprint 18, up from 162) now genuinely runs
  against a real Postgres 16 + Redis 7 instance — 199/199 passing. Running it
  for the first time surfaced a real bug (see Sprint 13) that every prior
  syntax-only check had missed, which is exactly the risk this gap always
  described.
- **Frontend and backend have never run simultaneously against each other**
  in this environment — only independently verified (backend boot, frontend
  build). The actual network integration between them is unverified until
  you run both together.
- Login UX still asks for a raw tenant UUID ("Organization ID") rather than
  resolving by slug/subdomain — flagged in Sprint 4, still unfixed.
- Resume *parsing* (as opposed to upload/storage) is deferred to Milestone 2
  per the original roadmap.
- Pipeline template creation has no frontend UI yet (create via API/curl) —
  the JobsPage dropdown only lets you *select* an existing template.

## Sprint 6 — Async infrastructure (Milestone 2 begins)

- Celery app with queue routing (`critical`/`cpu_intensive`/`default`/`batch`
  per Phase 15.1), initialized from Flask config in the app factory
- `EventBus` — the concrete Phase 7.8 decoupling: services publish named
  events (`resume.uploaded`, `application.stage_changed`) and know nothing
  about subscribers
- Resume parsing moved off the request path (async `parse_resume_task`, with
  an idempotency guard — real NLP/AI extraction deferred to the AI Assist
  milestone, only the async plumbing is real here)
- `Notification` model (with the CHECK constraint enforcing exactly one
  recipient type) + `NotificationService`, wired to two real automations:
  stage change → in-app notification for the recruiter, email notification
  for the candidate
- **Genuine Celery task execution in tests**: `CELERY_TASK_ALWAYS_EAGER=True`
  in `TestingConfig` runs tasks synchronously in-process, so the full event
  chain (stage move → publish → task → 2 notification rows) is actually
  testable without a live Redis broker or worker process
- Frontend: notification bell in the app shell header, polling every 30s,
  mark-as-read

**Three real bugs caught this sprint, not carried forward:**
1. `redis` package was missing from the dev venv despite being in
  `requirements/base.txt` — caught by the eager-mode Celery test actually
  failing with a real stack trace, not a silent pass.
2. `NotificationBell.jsx` had a wrong relative import path
  (`./useNotifications` instead of the actual location in
  `features/notifications/`) — caught by the real `npm run build`, not by
  reading the JSX.
3. `docker-compose.yml`'s `worker` service pointed the Celery CLI directly at
  `app.workers.celery_app.celery_app` — a bare, unconfigured instance, since
  `init_celery(app)` (which applies broker URL, eager mode, etc.) is normally
  only called inside `create_app()` for the web process. A standalone worker
  would have started with no broker config and silently failed to consume
  anything. Fixed with a dedicated `app/workers/worker_entrypoint.py` that
  bootstraps a Flask app, calls `init_celery()`, and imports every task
  module so they're registered — verified to actually resolve the broker URL
  and register all 4 tasks correctly.

**Known gap:** the stage-change notification chain is verified for syntax
and logical consistency (`tests/integration/test_notification_events.py`)
but — like every integration test in this project — hasn't executed against
a live Postgres in this sandbox.

## Sprint 7 — Interview management

- `Interview`/`InterviewPanelist`/`InterviewFeedback` models — interview kits
  and question banks (from the original Phase 9b design) are deliberately
  deferred to a later polish sprint, scoped out explicitly rather than
  forgotten
- `InterviewService`: schedule (snapshots the application's current pipeline
  stage), reschedule, cancel, submit/update structured rubric feedback
  (panelist-only, enforced — a non-panelist gets a real 403)
- `interview.scheduled` event wired into the Sprint 6 notification chain:
  in-app notification for each panelist, email confirmation for the candidate
- Frontend: schedule-interview action on each pipeline board card, "My
  Interviews" page with a rubric-builder feedback form

**A critical, previously undetected bug found and fixed this sprint:** the
access token issued by `/auth/refresh` was missing `tenant_id`/`role_id`
claims — present at login, silently dropped on every refresh. Since the
frontend's `AuthProvider` calls `/auth/refresh` unconditionally on every page
load (for silent session restore), **this meant every page reload since
Sprint 1 broke tenant context on the very next authenticated request.** It
went unnoticed until Sprint 7 needed to decode the JWT client-side for the
current user's ID, which is what exposed it. Fixed in
`AuthService._issue_access_token_from_claims`, with a dedicated regression
test (`test_refresh_preserves_tenant_context_for_subsequent_requests`) added
specifically because this class of bug is too easy to silently reintroduce.

**Another real gap fixed in passing:** `useAuth().user` was never actually
populated (flagged as a known gap back in Sprint 4) — fixed by decoding the
JWT's identity claim client-side rather than adding a new backend endpoint,
since the claim was already there.

**Known gap, stated plainly:** there's no user-directory API yet, so the
"Schedule Interview" UI can only default the panelist to the current user —
picking other panelists needs a `GET /api/v1/users` endpoint that doesn't
exist. Flagged in the code, not silently worked around.

## Frontend gap-fix batch (post-Sprint-7 review)

Reviewed every backend endpoint against actual frontend screens and found
several real gaps — endpoints that existed with no UI ever calling them.
Closed the two most blocking ones (a job could get stuck in
`pending_approval` forever with no UI to approve it; recruiters had no way
to reject an application):

- **New backend endpoint**: `GET /jobs/:id/approval-steps` — didn't exist at
  all; the frontend had no way to discover a step's ID to call `approve` on,
  so this had to be added before the UI fix was even possible.
- **JobPipelinePage**: approve-step panel (shown when `pending_approval`),
  close button (when `published`), archive button (when `closed`)
- **ApplicationCard**: reject action added alongside move-stage and
  schedule-interview

**Still open, stated plainly:** no frontend screens yet for
departments/teams, company settings, or pipeline template creation
(all backend+API only); no user-directory API (blocks proper
approver/panelist selection); login still asks for a raw tenant UUID;
no frontend permission-based UI hiding (buttons show even when the
backend will reject the action — it correctly blocks it, just not
proactively hidden client-side).

## Sprint 8 — Offers & onboarding (Milestone 4)

- `Offer`/`OfferApprovalStep` — deliberately mirrors `Job`/`JobApprovalStep`'s
  dedicated-table pattern rather than the polymorphic `approval_steps` table
  from the original Phase 9b design, since Sprint 3 already shipped the
  dedicated-table approach and refactoring both onto a shared table now would
  touch completed, working code for marginal DRY benefit — a deliberate
  consistency choice, documented in the model file itself
- Offer state machine (`draft→pending_approval→sent→accepted/rejected/withdrawn`)
  as an independent, unit-tested validator — 7/7 tests genuinely passing
- `offer.accepted` event wired into the Sprint 6 event bus, auto-creating an
  onboarding checklist with default tasks (the "If Offer Accepted → Trigger
  Onboarding" automation from the original spec) — verified end to end via
  `CELERY_TASK_ALWAYS_EAGER`
- Frontend: `OfferPanel` embedded in each pipeline application card
  (create → submit → approve → accept/decline), `OnboardingPage` with
  task-completion checkboxes

**A permission-design correction made before shipping, not after:**
`accept`/`decline`/`withdraw` initially used `offer.approve` (the internal
approval-chain permission) but that's semantically wrong — those actions
record the *candidate's* decision, entered by a recruiter, not an internal
approver's decision. Fixed to use `offer.create` instead, with a comment
explaining the distinction, since there's no authenticated candidate portal
for offers yet (a real, stated gap, not silently worked around).

## Sprint 9 — AI Assist layer (Milestone 5)

**No paid cloud AI provider is used anywhere in this project.** The AI Assist
layer runs on a local Ollama server (`llama3.1:8b` by default, fully
configurable) — no API key, no per-token billing, no external network
dependency for AI features. `docker-compose up` now includes an `ollama`
service; the model isn't bundled in the image and needs one manual pull:
```bash
docker-compose exec ollama ollama pull llama3.1:8b
```

- `BaseAIClient` / `OllamaAIClient` / `StubAIClient` in
  `app/services/ai/ai_client.py` — the exact same provider-abstraction shape
  already used for storage (`local`/`s3`) and email (`console`/`ses`).
  `AI_PROVIDER=ollama|stub`, selected via config exactly like every other
  provider in this codebase.
- **The service layer never knows which provider is active** — `JDImprovementService`
  and `MatchScoreService` only ever call `ai_client.complete(prompt)` and read
  back a generic `{text, input_tokens, output_tokens}` shape. Adding a future
  provider (Claude, OpenAI, Gemini, or anything else) means writing one more
  `BaseAIClient` subclass and one more branch in `build_ai_client()` — nothing
  else in the codebase changes.
- **JD Improvement**: `POST /ai/jobs/:id/improve-description` returns a
  suggestion and logs an `ai_requests` row with `status=suggested`; the job's
  actual `description` is **never** modified until a separate, explicit
  `POST /ai/jobs/:id/apply-description` call — the recruiter must accept or
  reject every suggestion, per the "AI assists, never decides" guardrail from
  Phase 6.7.
- **Match Scoring**: the numeric score is a **deterministic Python
  skill-overlap heuristic** (`compute_skill_overlap_score`) — never an LLM
  call. The AI layer only adds a one-sentence natural-language explanation on
  top. This is a deliberate design choice, not a shortcut: it means the score
  itself is fast, free, reliable, and fully unit-testable (6 genuinely
  executed tests) with zero dependency on any AI provider being available.
- `AIRequest` model/table logs every AI call for cost/audit purposes
  (`feature`, `entity_type`/`entity_id`, token counts, `status`).

**Testing note:** `TestingConfig` always forces `AI_PROVIDER=stub`, regardless
of what's configured elsewhere — tests must never depend on a local Ollama
server being installed or running wherever the suite executes.
`DevelopmentConfig` defaults to `ollama` so it works out of the box against
`ollama serve` locally. All 13 AI-client tests (including Ollama's HTTP call
shape, connection-refused/timeout/model-not-pulled error handling) mock
`requests.post` — genuinely executed, zero real network calls, same behavior
whether or not Ollama happens to be running wherever tests run. A dedicated
regression test explicitly confirms `anthropic`/`openai`/`gemini` are rejected
as unknown providers, so a paid provider can never be silently reintroduced.

## Frontend gap-fix batch #2 + Sprint 9 frontend completion

**New backend endpoint:** `GET /api/v1/users` — a genuine missing piece
(flagged since Sprint 7): there was no way to list colleagues for
panelist/approver selection. Read-only, open to any authenticated tenant
member.

**Frontend gaps closed:**
- `OrgPage` — departments and teams list + create (Sprint 2's missing UI)
- `CompanySettingsPage` — company name editing (Sprint 3.5's missing UI)
- `PipelineTemplatesPage` — a real stage-builder UI (add/remove stages with
  type + order, then create the template) — previously API-only since
  Sprint 3
- `ScheduleInterviewButton` rewritten to use the real user directory — a
  genuine multi-select panelist picker instead of defaulting to yourself
  with no alternative

**Sprint 9 frontend — found already written but never wired in:**
`useAI.js` and `JobDescriptionPanel.jsx` already existed in the codebase,
complete and correctly matching the backend schemas — but `JobPipelinePage`
imported both `JobDescriptionPanel` and `useComputeMatchScore` **without
ever rendering or calling them**. Dead imports, not working features. Fixed
by actually wiring both in:
- `JobDescriptionPanel` now renders on the job pipeline page — the real
  "✨ Improve with AI" → review-and-edit → accept-or-discard flow
- `MatchScoreBadge` (new) added to each `ApplicationCard` — "Compute match
  score" button showing the deterministic skill-overlap percentage plus the
  Ollama-generated one-sentence explanation

**A real bug caught mid-edit, not shipped:** my own rewrite of
`ScheduleInterviewButton` referenced `useUsers` without importing it — caught
by the mandatory `npm run build` step before packaging, same discipline that
has caught a real bug in nearly every batch of this project.

## Sprint 10 — Search, analytics, talent CRM (Milestone 6)

**Deliberate simplifications, stated plainly:** this sprint uses plain
`ILIKE` search and live-query analytics rather than Phase 18's
tsvector/GIN full-text search or Phase 19's three-tier
(live/materialized-view/nightly-batch) design. Both are genuinely correct
at this project's current scale — the documented thresholds (500K+
candidates for search, dashboard load competing with write traffic for
analytics) are where the added complexity becomes worth it, not before.
Swapping either out later changes only the service's internals, not any
caller.

- `TalentPool`/`TalentPoolMembership` — candidates never disappear after
  rejection; pools with add/remove, checked for accidental duplicate
  membership (a real 422, not a silent no-op or a duplicate row)
- `CandidateNote`/`CandidateTag` — added directly to `CandidateService`
  rather than a new service, since they're candidate-profile-scoped
  operations, not a distinct domain; tag-adding is idempotent by design
  (adding the same label twice is a no-op, not an error)
- `SearchService` — cross-entity search (candidates by name/email, jobs by
  title) in one call
- `AnalyticsService` — hiring funnel (stage-by-stage candidate counts for a
  job), time-to-hire (avg days from `applied_at` to accepted-offer
  `responded_at`), recruiter volume
- New backend endpoint: `GET /api/v1/users` (a real gap closed in passing —
  needed for the "add candidate to pool" flow's data model, though the pool
  UI currently adds candidates from the Candidates page directly)
- Frontend: Talent Pools page, expandable notes/tags panel on each candidate
  row (a real React bug caught and fixed — the `<>` fragment shorthand can't
  carry a `key` prop, which React requires for list items; fixed with
  explicit `Fragment` import), a live search bar in the app header, and an
  Analytics dashboard with a CSS-based funnel bar chart (no charting library
  dependency needed for this scope)

## Sprint 11 — Admin, audit, hardening (Milestone 7) — **all planned milestones complete**

**Deliberate simplification, stated plainly:** `AuditLog` is a single,
unpartitioned table rather than Phase 9b's monthly-partition design.
Genuinely correct at this project's current scale — partitioning earns its
complexity once write volume causes real query/retention problems, which
isn't true yet. The column shape matches the original design exactly, so
partitioning later is a migration-only change.

- `AuditLog`/`AuditService` wired into the highest-value compliance actions:
  every Job status transition, Application rejection, Offer accept/decline,
  and admin user-status changes — not universal instrumentation of every
  write in the system (a deliberate scope choice, not an oversight)
- Admin endpoints (`admin.manage_users`-gated): list company users, change a
  user's status (active/locked/disabled) with an automatic audit entry,
  browse the audit log, a system health check (DB reachability, user count,
  active job count)
- **Security hardening fix**: the search endpoint (`GET /search`) had no
  rate limit — every other write-adjacent or costly endpoint in the project
  does. Added `30 per minute`, closing a real gap found during this sprint's
  review rather than assumed-fine.
- Frontend: tabbed Admin page (Users / Audit Log / System Health)

**Scope note:** true platform-wide Super Admin (cross-tenant administration)
from the original Phase 4 design was not built — every admin action here is
scoped to the acting admin's own company, consistent with how every other
feature in this project works. Cross-tenant platform administration would be
a materially different feature (a separate admin identity model entirely
outside normal tenant scoping) and is out of scope for this milestone.

**This closes out all 7 milestones from the original roadmap** (Phase 22).
Remaining work is the accumulated frontend-debt list below, not new
functionality.

## Gap-fix batch — real usability blockers, not new features

- **Critical fix: company signup.** There was previously no way to create a
  Company/org_admin short of manually inserting DB rows. `POST /auth/signup`
  now does this atomically. New users activate immediately — no
  email-verification flow exists yet to ever move a "pending" user to
  active, so leaving them pending would have locked them out forever. Stated
  MVP simplification, not an oversight.
- **Login no longer takes a raw tenant UUID.** `login`/`register` now
  resolve tenant by `company_slug` in the request body. The generic
  "Invalid organization, email, or password" error covers all three failure
  cases so the login form can't be used to enumerate valid org slugs.
- **Frontend permission-based UI hiding.** New `GET /auth/permissions`
  endpoint; the frontend hides (not just disables-after-fail) actions the
  current user's role can't perform — New Job, Add Candidate, Approve,
  Close/Archive, and the Admin nav link.
- **Pagination**, implemented once in `app/utils/pagination.py` and applied
  to candidates, jobs, notifications, and audit logs — page/per_page params,
  100-item cap, `meta.pagination` in the response. Frontend Prev/Next wired
  into the Candidates and Jobs pages.


## Sprint 12 — Org structure, invitations, approvals & Employee Referral Portal

Present in the codebase (migrations `0013`-`0016`) but never written up
here — documenting the gap rather than leaving it:

- Org structure extensions (departments/teams/locations groundwork)
- User invitation flow
- Generic approval-chain workflow (`ApprovalChain`), reused by job and
  offer approval steps
- **Employee Referral Portal** (`api/v1/employee_portal`,
  `services/referral_service.py`, `models/referral.py`) — lets an
  internal employee (a `User`) browse open jobs and refer a candidate;
  a `Referral` links the referring employee to the `Application` it
  produced. Deliberately no `referrals.status` column — status is read
  from the linked application at query time so there's no second copy
  of "where did this candidate end up" that could drift from the real
  pipeline state.

## Sprint 13 — V2 Performance: Candidate Ranking Pipeline

Full detail, design rationale, and real measured benchmark numbers in
[`docs/ranking-engine.md`](docs/ranking-engine.md). Summary:

- `rank_candidates_for_job` was a synchronous loop calling the AI client
  once per active applicant, unconditionally, inline in the HTTP
  request. Rebuilt as: deterministic pre-filter (skill overlap +
  experience band) → cached AI scoring (explanation reused across
  candidates who share a skill signature on the same job) → sorted,
  instrumented results.
- New async path (`POST /ai/jobs/:id/rank-candidates/async`, Celery,
  `batch` queue) + `GET /ai/ranking-jobs/:id` polling, for applicant
  pools too large to score inline. The original synchronous endpoint is
  unchanged in contract — this is additive, not a breaking change.
- `Flask-Caching` was registered in the app factory but never actually
  used anywhere in the codebase (`CACHE_TYPE` was unset, defaulting to
  a no-op backend) — wired to Redis for real.
- Reproducible benchmark: `python scripts/benchmark_ranking.py`.
  Measured (stub AI provider, real Postgres+Redis): **95-99.5% of AI
  calls avoided** across 100/500/1,000-candidate runs, with 33-40% of
  each seeded pool caught by the pre-filter before ever reaching
  scoring. See the doc above for the full table and for why the
  duration-improvement numbers specifically should be re-measured
  against a real Ollama server before quoting them anywhere.
- 23 new tests (pre-filter behavior, cache-hit accounting, async job
  status, cross-tenant 404 on the new async endpoint); full suite run
  against real infrastructure: **185/185 passing, zero regressions**.

**One real bug caught, not carried forward:** seeding data for the
benchmark above — plain `Candidate(...)` construction through the ORM,
nothing unusual — failed with a Postgres NOT NULL violation on
`created_at`, against a database built via the actual `flask db
upgrade` migration chain (not the test suite's `db.create_all()`).
Root cause: 24 timestamp columns across migrations `0001`-`0012` were
missing the `server_default=now()` their own models declare — a
genuine migration/model drift that the "Known gaps" entry above (tests
never running against a live, migration-built Postgres) had been
masking since Sprint 1. Fixed in
`migrations/versions/0017_fix_timestamp_defaults.py`, applied and
verified against a real Postgres instance. Full writeup in the
Appendix of `docs/ranking-engine.md`.

## Sprint 14 — V2 Performance: Database Profiling & Indexing

Full detail, real `EXPLAIN ANALYZE` numbers, and a documented reverted
regression in [`docs/database-optimization.md`](docs/database-optimization.md).
Summary:

- New `scripts/generate_synthetic_data.py` — bulk-insert, funnel-shaped
  synthetic dataset generator (100K/300K+ candidates in ~25-90s).
- **Correction to Phase 0**: that assessment claimed zero explicit
  indexes existed anywhere — a bad grep (`sa.Index()`/`index=True`),
  not a bad schema. The project actually declares 25 indexes via
  `op.create_index(...)`, several already matching real query shapes.
  Documented, not swept under the rug.
- Found and fixed a real correctness bug: `GET /api/v1/jobs` and
  `GET /api/v1/candidates` paginated with no `ORDER BY` — non-deterministic
  pages. Fixing it exposed a real cost (unindexed sort), fixed with
  `idx_candidate_profiles_company_created`: **31ms → 0.09ms** shallow
  page, **71ms → 17.6ms** deep page, confirmed against a real second
  tenant.
- Found a plausible-looking inefficiency in `AnalyticsService.
  pipeline_health()` (an unscoped multi-tenant aggregation), implemented
  the "obvious" fix, measured it against a genuine second tenant, found
  it was **slower** (137ms vs 89ms — an existing index already made the
  unscoped version cheap), and reverted it. Documented as the actual
  lesson, not hidden.
- Measured `ILIKE` search cost at 100K candidates against the project's
  own stated 500K+ threshold for full-text search: fine on the common
  path (4.6ms), 139ms on a real, common worst case (no-match query) —
  a data point for that threshold, not a contradiction of it.

## Sprint 15 — V2 Performance: Analytics Dashboard Caching

Full detail and real benchmark numbers in
[`docs/caching.md`](docs/caching.md). Summary:

- `AnalyticsService.executive_summary()` — the single most expensive
  analytics read (five live aggregate queries every call) — is now
  cached in Redis, keyed per tenant, with a 60s TTL as a safety net
  and active invalidation on `application.stage_changed` and
  `offer.accepted` (new Celery task, wired through the existing
  `EventBus`, same pattern as the notification subscribers).
- Measured (real Postgres 16 + Redis 7, both Phase 2 datasets):

  | Dataset | Without cache (p50) | Cache hit (p50) |
  |---|---:|---:|
  | 100K candidates | 260 ms | **0.03 ms** |
  | 300K candidates | 723 ms | **0.03 ms** |

  A cache hit costs one Redis round trip instead of five SQL
  aggregates — hit latency barely moves between the 100K and 300K
  datasets while the uncached latency scales with data volume.
- Honest known gap: job status changes (published/closed) aren't
  actively invalidated — no event exists yet for that path, so the 60s
  TTL is what bounds staleness there, not active invalidation. Stated
  plainly in `docs/caching.md` rather than left implicit.
- 4 new tests (cache-key scoping, hit/miss reporting, invalidation on
  stage change via the real event path, invalidation task correctness
  for offers). Full suite: **191/191 passing.**

## Sprint 16 — V2 Performance: Search Optimization

Full detail, including two subtle real bugs found along the way, in
[`docs/search-optimization.md`](docs/search-optimization.md). Summary:

- Corrected a scoping assumption in `SearchService`'s own documented
  500K+ ILIKE threshold: `candidates` is a deliberately **global**
  table (shared identity across tenants), so the count that matters is
  global, not per-tenant. With Phase 2's second tenant's data actually
  present (402,120 global candidates), the real worst-case search cost
  was 530ms, not the 139ms measured against one tenant in Phase 2.
- Added `pg_trgm` GIN indexes (migration `0019`) — but that alone
  changed nothing. Two more real bugs had to be found first:
  1. The natural `JOIN`-shaped query never let Postgres use the new
     indexes, regardless of `enable_seqscan`. Fixed by restructuring
     to a behaviorally identical semi-join (`candidate_id IN (SELECT
     ...)`).
  2. `email` is `CITEXT`; an uncast `ILIKE` against it doesn't match
     an index built on `email::text` — and Postgres doesn't partially
     use a `BitmapOr`, so that one unindexable branch silently made
     it abandon indexing first_name/last_name too. Found by running
     the actual SQLAlchemy-generated SQL through `EXPLAIN ANALYZE`,
     not a hand-written equivalent.
- Measured end to end, through the real application code path:
  **530ms → ~1.3ms** for the no-match case, at 402K global candidates.
- Decision, not a foregone conclusion: stayed on `ILIKE` + `pg_trgm`
  rather than moving to tsvector/Elasticsearch — Postgres-native,
  preserves exact current search semantics, and now performs
  comparably to what a heavier engine would offer at this scale.
- 1 new regression test (email-substring search — the exact case the
  CITEXT bug broke). Full suite: **192/192 passing.**

## Sprint 17 — V2 Performance: Load Testing & Horizontal Scalability

Full detail and an honest sandbox-resource caveat in
[`docs/scalability.md`](docs/scalability.md). Summary:

- Two real bugs found before load testing could even meaningfully
  start: the Docker image ran `flask run` (the single-threaded dev
  server) instead of the `gunicorn`/`gevent` already listed in
  requirements — including correcting an unverified claim from my own
  Phase 0 assessment, which assumed gunicorn was wired up without
  checking the Dockerfile; and Flask-Limiter had no storage backend
  configured, silently defaulting to in-memory counters that don't
  work correctly across multiple workers/replicas. Both fixed
  (gunicorn+gevent in the Dockerfile CMD; `RATELIMIT_STORAGE_URI` on
  Redis, same pattern as Phase 1's cache fix).
- A third bug found once testing actually started: the rate limiter's
  default IP-based key collapsed all concurrent users behind one
  shared IP into a single bucket — measured 31-37% of `/search`
  requests rejected with 429s at just 10-50 simulated users, far below
  any real capacity limit. Fixed: rate limits now key by authenticated
  JWT identity, falling back to IP only for pre-auth endpoints
  (login's own brute-force protection, verified still IP-keyed and
  still triggering correctly).
- Real Locust load test (`loadtest/locustfile.py`, realistic weighted
  endpoint mix) against the real gunicorn server and the Phase 2
  100K-candidate dataset, at 10/50/150 concurrent users — 0% errors at
  every tier once rate limiting was isolated out; a genuine
  throughput/latency inflection point between 50 and 150 users.
  **Stated plainly, not glossed over: this sandbox has exactly 1 CPU
  core**, so the absolute numbers aren't a production capacity claim —
  the doc says so directly and gives the exact commands to re-run on
  real infrastructure.
- Statelessness reasoned through explicitly (JWT-only auth, Redis-
  shared cache and rate limiter across all 4 worker processes) rather
  than just assumed from a clean load-test run.
- 2 new tests (rate-limit key function: falls back to IP correctly
  with no JWT or an invalid one). Full suite: **194/194 passing.**

## Sprint 18 — V2 Performance: Observability

Full detail in [`docs/observability.md`](docs/observability.md).
Summary:

- `/health` actually checks Postgres and Redis now (was an
  unconditional `{"status": "ok"}` before — checked nothing).
- `/metrics` (Prometheus text format): HTTP request counters/duration,
  the Phase 1 ranking pipeline's real metrics, the Phase 3 dashboard
  cache's hit/miss counts, and stage transitions. Deliberately no
  `sla_breaches_total` — no SLA engine exists in this codebase to back
  that metric with real data.
- Real subtlety caught and fixed: `prometheus_client`'s default
  registry is per-process, which silently under-reports behind Phase
  5's 4 real gunicorn workers. Fixed via documented multiprocess mode
  (`gunicorn.conf.py`) and verified by actually running 4 workers,
  sending 21 requests, and confirming `/metrics` reported 21 — not a
  quarter of that.
- 5 new tests. Full suite: **199/199 passing.**




### Backend
```bash
cd backend
cp .env.example .env
cd ../infra
docker-compose up --build
docker-compose exec backend flask db upgrade
docker-compose exec backend flask seed-roles
docker-compose exec ollama ollama pull llama3.1:8b   # one-time, before AI features work
```

`flask seed-roles` must run before anyone can sign up — signup looks up the
system `org_admin` role by name and fails clearly if it isn't seeded yet.
After that, creating your first organization is `POST /api/v1/auth/signup`
(or the Signup page in the frontend) — no manual DB row insertion needed
anymore.

Twelve migrations exist (`0001` through `0012`), all hand-written (no live
Postgres was available in the build environment) and cross-checked
column-by-column against the SQLAlchemy models programmatically. Still worth
a `flask db check` against your real Postgres before trusting blindly in a
shared environment.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`, proxying `/api` to `http://localhost:5000` —
the backend needs to be running via docker-compose for the frontend to
actually work end to end.

Public career portal (once both are running): `http://localhost:5173/careers/<company-slug>`

## Running tests

```bash
docker-compose exec backend pip install -r requirements/dev.txt
docker-compose exec backend pytest
```

- `tests/unit/` — 64 tests, genuinely executed and passing (repository
  tenant-scoping guard, job/offer state machines, file upload magic-byte
  validation, AI client/Ollama HTTP mocking, pagination math, the V2
  candidate pre-filter, ranking-metrics helpers, and the rate-limit key
  function)
- `tests/integration/` — 135 tests: auth flow (incl. signup), tenant
  isolation, job lifecycle, company settings, candidate/resume, interviews,
  offers/onboarding, notifications, talent CRM/search/analytics, admin/audit,
  pagination, the Milestone 1 E2E test, the V2 ranking pipeline, and analytics
  caching — **199/199 tests total, genuinely run against a real Postgres 16 +
  Redis 7 instance** (see Sprint 13/14/15/16/17/18)

## Quick manual check

```bash
curl http://localhost:5000/health
# {"status": "ok"}
```

## Next up (Sprint 6+, not in this package)

Interview management, offers, and the AI assist layer, per the original roadmap.
