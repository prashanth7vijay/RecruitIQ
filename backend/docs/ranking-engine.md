# Candidate Ranking Pipeline (V2)

## 1. Problem

`POST /ai/jobs/:id/rank-candidates` scored every active applicant on a
job by calling the AI client synchronously, one candidate at a time,
inside the HTTP request. There was no pre-filter (an applicant with
zero overlap with the job's required skills still got a full AI call),
no de-duplication (two candidates with identical skill sets each paid
for their own AI call even though the explanation would be identical),
and no way to run it as anything but a blocking request — fine for a
handful of applicants, not for a real applicant pool.

## 2. Existing behavior (pre-V2)

```
active applications -> for each: call ai_client.complete() -> persist score
```

Every application, unconditionally, one AI call each, inline in the
request.

## 3. Bottleneck

The AI call, not the deterministic part. `compute_skill_overlap_score()`
is pure Python — negligible cost. The AI explanation call is the
expensive step, and it was being paid for by every applicant regardless
of whether they were remotely qualified, and regardless of whether an
identical explanation had already been generated for someone else on
the same job.

## 4. Design decision

```
active applications
    -> deterministic pre-filter (required-skill overlap, experience band)
    -> scoring, with the AI explanation cached per
       (tenant, required-skills-signature, candidate-skills-signature)
    -> sorted results + RankingRunMetrics
```

- **Pre-filter** (`app/services/ai/candidate_filter.py`) is pure,
  dependency-free, unit-tested on its own. It only ever adds candidates
  to the "skip AI, no score this run" bucket — it never removes anyone
  from the applicant list itself. Missing data (no stated experience
  years, no job-level experience band) never filters someone out; only
  a known, explicit mismatch does.
- **Cache** reuses an AI explanation across any two candidates who
  share an identical (job, skill-set) signature — this is the more
  effective lever of the two: two structurally distinct candidates
  filling the same role usually cluster into a handful of common skill
  combinations, so this is where most of the real savings come from
  (see benchmark below — 95-99%+ AI calls avoided, vs. filtering out
  roughly a third to 40% of the pool).
- **Async path** (`app/workers/ranking_tasks.py`, routed to Celery's
  `batch` queue) runs the identical pipeline off the request thread for
  pool sizes where blocking a request isn't acceptable, polled via
  `GET /ai/ranking-jobs/:id`.

## 5. Alternatives considered

- **Batch the AI calls concurrently instead of caching them** — doesn't
  reduce the number of AI calls made, only their wall-clock cost; still
  pays for N calls when only a handful of distinct explanations exist.
  Caching and bounded concurrency aren't mutually exclusive, but caching
  is the higher-leverage first step and was implemented first.
- **Cache the numeric score too, not just the explanation** — not done:
  the score is a cheap, pure-Python computation already; caching it
  would save nothing measurable and would add a second cache-invalidation
  surface for no benefit.
- **Reject filtered-out candidates outright (change their application
  status)** — rejected as a design: the pre-filter is a ranking-run
  decision ("don't spend an AI call on this pass"), not a hiring
  decision. A recruiter can still see and act on every applicant; the
  filter only withholds a scoring pass, never the pipeline stage.

## 6. Implementation

See `app/services/ai/match_score_service.py`,
`app/services/ai/candidate_filter.py`,
`app/services/ai/ranking_metrics.py`, `app/workers/ranking_tasks.py`.

`compute()` (used by both the pipeline and the standalone
`/match-score` endpoint) still writes exactly one `AIRequest` audit row
per call whether or not the explanation was served from cache — an
`AIRequest` row records "this application was scored," not "a network
call happened." What the cache actually skips is the call to
`ai_client.complete()`, which is what `ai_calls_made` /
`ai_calls_cached` in `RankingRunMetrics` measure directly.

## 7. Benchmark methodology

`scripts/benchmark_ranking.py`. For each requested dataset size, seeds
an identical dataset twice (fixed random seed, so the shape is
reproducible run to run):

- ~40% of candidates get a deliberately non-overlapping skill set (the
  pre-filter's target)
- the rest draw from a small fixed pool of 5 skill combinations (what
  makes the cache do anything)

Then runs, over that identical dataset:

- **Baseline** — every application scored via `compute()` directly, no
  filter, no cache (`MatchScoreService(cache=None)`), matching the
  pre-V2 loop exactly.
- **Optimized** — `rank_candidates_for_job(force=True)`, the current
  pipeline, cache live.

Run with `python scripts/benchmark_ranking.py --sizes 100,500,1000`.
`--ai-provider stub` (default) uses the deterministic in-process stub
client — no real Ollama server required, and the right choice for
measuring pipeline/cache mechanics in isolation. Pass
`--ai-provider ollama` to measure against a real local Ollama server;
expect a much larger duration gap there, since what's being skipped on
a cache hit is a real network call, not a fast stub function.

## 8. Results (measured, stub AI provider)

| Candidates | Baseline duration | Optimized duration | Duration change | AI calls (baseline → optimized) | AI calls avoided | Filtered out |
|---:|---:|---:|---:|---:|---:|---:|
| 100  | 0.640 s | 0.527 s | -17.7% | 100 → 5 | 95.0% | 37 / 100 |
| 500  | 3.537 s | 2.918 s | -17.5% | 500 → 5 | 99.0% | 191 / 500 |
| 1000 | 9.225 s | 6.708 s | -27.3% | 1000 → 5 | 99.5% | 394 / 1000 |

Reproduced by running `python scripts/benchmark_ranking.py --sizes 100,500,1000`
against a real Postgres 16 + Redis 7 instance on 2026-09-22.

**Reading these numbers honestly:** with the stub AI client, an AI
"call" is a fast in-process function, so the duration gap here is
mostly pipeline/DB overhead, not AI latency — the wall-clock
improvement (17-27%) understates what this would look like against a
real, slow AI provider. **AI calls avoided (95-99.5%) is the number
that transfers directly to a real deployment** — it's a property of
how many distinct skill-signature clusters exist in the pool, not of
which AI provider answers them, and it would translate to the same
percentage reduction in real Ollama calls (and real latency, at
whatever Ollama's real per-call cost is) in production.

Re-run with `--ai-provider ollama` against a real local Ollama server
for the corresponding real-latency numbers before using those in a
resume bullet — the AI-calls-avoided percentage above is legitimate
either way, but a duration/throughput claim should come from the
provider it'll actually be attributed to.

## 9. Trade-offs

- The cache is explanation-only, keyed on skill signature — it doesn't
  account for anything else that might make two "same skills"
  candidates meaningfully different to an AI explanation (seniority
  framing, resume tone). Acceptable here since the explanation's job is
  "why do these skills matter for this role," not a candidate-specific
  narrative.
- Cache entries have a 3600s TTL and no explicit invalidation on
  `required_skills` change — a job whose requirements change mid-run
  will naturally produce new cache keys (the signature includes
  required_skills), so stale entries just age out unused rather than
  needing an active invalidation path.
- The async endpoint's job-status polling rides on Celery's own result
  backend rather than a dedicated `ranking_jobs` table — simpler, no
  migration, and sufficient for polling a single job's status; a
  dashboard of "all ranking runs across the company" would need an
  actual table, which this doesn't provide.

## 10. Future improvements

- Bounded-concurrency AI calls (e.g. a small worker pool inside the
  task) for the cache-miss portion, once real Ollama latency numbers
  justify it.
- A `ranking_jobs` table if multi-run visibility/audit ever becomes a
  real requirement, per the trade-off above.
- Extend the pre-filter with a configurable minimum-overlap threshold
  (currently "at least one required skill") if a real applicant pool
  shows that's too permissive at scale.

---

## Appendix: a bug this work surfaced

While seeding data for the benchmark above (creating `Candidate` rows
through the ORM against a database built by `flask db upgrade`, not
by the test suite's `db.create_all()`), every insert into
`candidates` — and, it turned out, into 23 other tables — failed with
a Postgres `NOT NULL` violation on `created_at` (or `applied_at` /
`uploaded_at` / `added_at`).

Cause: 24 timestamp columns across migrations `0001`-`0012` were
declared `nullable=False` with **no** `server_default`, even though
every corresponding SQLAlchemy model declares
`server_default=db.func.now()` for that column. Migrations `0013`,
`0015`, and `0016` (written later) already include the default
correctly — the bug looks like it was found and fixed going forward at
some point, but never backported to the earlier migrations.

It went undetected because the entire test suite builds its schema via
`db.create_all()` (which reads `server_default` correctly straight from
the model), never via `flask db upgrade` — so nothing in CI or the test
suite ever exercised the actual migration files a real deployment
would run. It surfaced the moment something (this benchmark script)
created data against a database built the way production actually
would be.

**Fixed in `migrations/versions/0017_fix_timestamp_defaults.py`** — an
`ALTER COLUMN ... SET DEFAULT now()` for all 24 affected columns,
applied and verified against a real Postgres instance (confirmed via
`information_schema.columns`), with the full test suite re-run
afterward (185/185 passing, no regressions).
