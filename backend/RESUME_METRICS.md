# RESUME_METRICS.md

Every number below was measured against a real Postgres 16 + Redis 7
instance, with real seeded data (Phase 2's `bench-100k` /
`bench-noise` datasets: 100K and 300K candidates respectively). None
is estimated, projected, or rounded up for effect. Full methodology
for each lives in the linked doc — re-run the linked script yourself
before trusting any number enough to say it in an interview.

---

### 1. Candidate ranking: AI calls avoided via pre-filtering + caching

**Value:** 95–99.5% of AI calls avoided across 100/500/1,000-candidate
ranking runs, with 33–40% of each pool caught by a deterministic
pre-filter before ever reaching the AI step.
**Benchmark:** `scripts/benchmark_ranking.py`
**Dataset:** synthetic, 100/500/1,000 candidates (fixed random seed)
**Before:** every active application scored unconditionally, one AI
call each (100/500/1,000 calls)
**After:** 5 AI calls total at every scale (skill-signature caching +
pre-filter)
**How measured:** baseline vs. optimized run over the identical
seeded dataset, real Ollama-compatible stub client
**Relevant code:** `app/services/ai/match_score_service.py`,
`app/services/ai/candidate_filter.py`
**Doc:** `docs/ranking-engine.md`
**Caveat:** measured with the stub AI provider — re-run with
`--ai-provider ollama` for a real-latency duration number; the
AI-calls-avoided percentage itself is provider-independent.

### 2. Database: paginated query latency via composite indexing

**Value:** candidate list pagination — 31ms → 0.09ms (shallow page),
71ms → 17.6ms (deep page, `OFFSET 80000`)
**Benchmark:** `EXPLAIN ANALYZE`, direct
**Dataset:** 100K + 300K candidates (two real tenants, 402K total)
**Before:** unindexed sort on every page load (also fixed a real
non-determinism bug: missing `ORDER BY` on the same endpoint)
**After:** `idx_candidate_profiles_company_created` composite index
**How measured:** `EXPLAIN ANALYZE` before/after, confirmed stable
with a second, independently-sized tenant present
**Relevant code:** `migrations/versions/0018_candidate_profiles_idx.py`
**Doc:** `docs/database-optimization.md`

### 3. Analytics dashboard: caching the most expensive read

**Value:** executive-summary dashboard p50 latency — 260ms → 0.03ms
(100K dataset), 723ms → 0.03ms (300K dataset)
**Benchmark:** `scripts/benchmark_analytics_cache.py`
**Dataset:** 100K and 300K candidates
**Before:** 5 live SQL aggregate queries on every dashboard load
**After:** Redis cache, tenant-scoped key, 60s TTL + active
invalidation on the 2 events that change the underlying data
**How measured:** p50/p95/p99 across 50 calls, with-cache vs.
without-cache, real Redis
**Relevant code:** `app/services/analytics_service.py`
**Doc:** `docs/caching.md`

### 4. Search: fixing a query the ORM generated that silently bypassed its own new index

**Value:** worst-case candidate search — 530ms → ~1.3ms (measured
through the real application code path, not raw SQL)
**Benchmark:** direct timing via `SearchService._search_candidates`
**Dataset:** 402,120 candidates (global — see the doc for why that
scoping mattered)
**Before:** unindexed `ILIKE`, JOIN-shaped query
**After:** `pg_trgm` GIN indexes + a semi-join restructure + an
explicit `CITEXT`→`TEXT` cast (both were required; neither alone
fixed it — see the doc for the two-bug debugging path)
**How measured:** timed calls through `SearchService` itself, not a
hand-written equivalent query
**Relevant code:** `app/services/search_service.py`,
`migrations/versions/0019_candidates_trgm_idx.py`
**Doc:** `docs/search-optimization.md`

### 5. A correctly-scoped fix that turned out to be a regression — caught before shipping

**Not a performance win — included because catching this is the more
valuable engineering signal.** An unscoped multi-tenant analytics
subquery looked like an obvious inefficiency; the "fix" (scope it to
one tenant before aggregating) measured **slower** against a real
second tenant (137ms vs. 89ms — an existing index already made the
"wasteful" version cheap). Reverted, with the reasoning kept in the
codebase rather than silently dropped.
**Doc:** `docs/database-optimization.md` §5

### 6. Load testing: real infrastructure bugs found before any load number meant anything

**Value:** not a single number — three real, distinct bugs found and
fixed before/during load testing: (1) the Docker image ran the
single-threaded Flask dev server instead of the gunicorn+gevent
already listed as a dependency; (2) the rate limiter had no storage
backend, silently defaulting to in-memory (broken across multiple
workers/replicas); (3) the rate limiter's IP-based key caused
31–37% of concurrent search requests to be falsely rejected with 429s
at just 10–50 simulated users.
**Doc:** `docs/scalability.md`
**Caveat, stated plainly:** the load test itself ran on a single-CPU-
core sandbox — the 3 bug fixes above are real and portable; the
absolute req/sec numbers in the doc are not a production capacity
claim.

---

## Suggested resume bullets

Only using what's above — pick what fits your format, don't stack all six:

> Rebuilt an AI candidate-ranking pipeline with deterministic pre-filtering and response caching, eliminating 95–99.5% of AI calls across benchmarked runs of 100–1,000 candidates.

> Diagnosed and fixed a full-text search regression spanning an ORM query-shape issue and a CITEXT/index type mismatch, cutting worst-case search latency from 530ms to ~1ms at 400K+ records.

> Added Redis caching to a recruiting analytics dashboard, cutting p50 latency from 260–723ms to 0.03ms across two real datasets, with tenant-scoped invalidation on write events.

> Found and fixed 3 production-readiness gaps during load testing (dev server in prod config, in-memory rate limiting, IP-based rate-limit collisions) before they could affect real users.

> Practiced evidence-based optimization: reverted a plausible-looking database fix after measuring it as a regression against real multi-tenant data, rather than shipping on intuition.
