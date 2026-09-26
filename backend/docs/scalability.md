# Load Testing & Horizontal Scalability (Phase 5)

## 1. Two real bugs found before load testing could even start

Setting up load testing — actually running the app the way it would
run in production, rather than through pytest's test client — surfaced
two real gaps that would have made any load test numbers misleading if
fixed after the fact instead of before:

**The Docker image never actually ran gunicorn.** `infra/docker/
backend.Dockerfile`'s `CMD` was `flask run` — the single-threaded Flask
development server — despite `gunicorn` and `gevent` being listed in
`requirements/base.txt` and my own Phase 0 assessment claiming
"backend (Gunicorn+gevent)" in its architecture inventory. That claim
was never actually verified at Phase 0 time; it was an assumption from
seeing gunicorn in requirements, not from reading the Dockerfile. Fixed
here: `CMD ["gunicorn", "--worker-class", "gevent", "--workers", "4",
"--bind", "0.0.0.0:5000", "wsgi:app"]`. Load-testing the dev server
instead would have measured Werkzeug's single-threaded request
handling, not this application's actual concurrency behavior.

**Flask-Limiter had no storage backend configured**, so it silently
used in-memory counters (its own warning, visible in this project's
test output before this fix: *"Using the in-memory storage... not
recommended for production use"*). In-memory means each gunicorn
worker — let alone each horizontally-scaled container — enforces its
own independent rate limit; a client effectively gets
`limit × workers × replicas` requests through, not the configured
limit. Fixed: `RATELIMIT_STORAGE_URI = REDIS_URL` (`app/config.py`) —
Redis was already a hard dependency for Celery and the Phase 1/3
caches, so this is Rule 10 (prefer existing infra) again, not a new
piece of infrastructure.

## 2. A third bug found once testing actually started

With rate limiting correctly Redis-backed and therefore correctly
*enforced* across workers, running Locust against the real server
immediately surfaced a different problem: **31–37% of `/search`
requests rejected with 429s** at just 10–50 simulated concurrent users
— far below any real capacity limit. Cause: the rate limiter's default
`key_func` is `get_remote_address` (keys by IP). Every simulated user
in the load test — and, in production, every real user behind a
shared office network, VPN, or NAT — shares one IP, so they all
collapse into one rate-limit bucket and throttle each other, even
though they're different people making entirely reasonable individual
request volumes.

Fixed in `app/extensions.py`: `Limiter`'s `key_func` now resolves the
authenticated user's JWT identity when one is present, falling back to
IP only for unauthenticated endpoints (login, register) — where
IP-based throttling is the actual intended brute-force defense, not an
accident. Verified `/login`'s lockout still triggers correctly (still
IP-keyed, since there's no JWT yet at that point) — 12 rapid bad-
password attempts still produced 429s after the lockout threshold.

**Honest limitation of this fix's own verification:** this load test's
simulated users all share a single JWT (see Section 4 — logging in per
simulated user would hit `/login`'s own rate limit and measure that
instead of search capacity), so re-running the exact same load test
against the identity-keyed limiter would show the *same* collapse —
all requests resolve to one identity, not many. The fix is verified at
the unit level (`tests/unit/test_rate_limit_key.py` — falls back to IP
correctly with no JWT or an invalid one) and by direct reasoning about
what `get_jwt_identity()` vs `get_remote_address()` key on, not by a
load test with genuinely distinct per-user tokens. A real follow-up
load test with N distinct logged-in users (see Section 6) would be the
way to actually measure this fix's effect under concurrency.

## 3. Statelessness — checked, not assumed

Per Rule 11 ("optimize based on profiling, not assumptions"), Section
16 of the original brief, and this project's own established habit of
distrusting unverified claims (see Section 1): every request in every
load test run below was served correctly and identically regardless
of which of the 4 gunicorn worker *processes* happened to pick it up
— auth is JWT-only (no server-side session store to be sticky about),
and both the Phase 1/3 cache and the Phase 5 rate limiter now share
one Redis instance across all workers. 0% error rate across all three
rate-limiting-disabled runs below is consistent with — not, on its
own, a rigorous proof of — safe multi-worker operation; the stronger
evidence is architectural (nothing in the request path reads or writes
process-local state).

## 4. Load test methodology

`loadtest/locustfile.py` — a realistic weighted mix (search 35%,
candidate list 25%, jobs list 20%, executive summary 15%, pipeline
health 5%), not hammering one endpoint. All simulated users share one
JWT, fetched via one real `/auth/login` call before Locust starts
(logging in per simulated user would hit `/login`'s own 10-per-minute
limit and measure that, not the endpoints under test — a real client
caches its token the same way). Run against the real gunicorn server
from Section 1, pointed at Phase 2's `bench-100k` dataset (100K
candidates) so every request does real work.

```bash
export RATELIMIT_ENABLED=false   # isolates raw capacity from Section 2's fix
gunicorn --worker-class gevent --workers 4 --bind 127.0.0.1:5000 wsgi:app &
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"company_slug":"bench-100k","email":"bench@example.com","password":"<real password>","remember_me":false}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")
LOAD_TEST_TOKEN=$TOKEN locust -f loadtest/locustfile.py --headless \
  -u 50 -r 10 -t 20s --host http://127.0.0.1:5000 --csv=loadtest/results/r50
```

## 5. Results — and an honest caveat about where these were measured

**This container has exactly 1 CPU core** (`nproc` → `1`). Postgres,
Redis, all 4 gunicorn workers, and Locust itself all competed for that
one core throughout every run below. The *relative* pattern (a real
throughput/latency inflection point exists somewhere in this range;
zero errors even under saturation; the rate-limit fix's correctness)
is meaningful. **The absolute numbers are not representative of a real
multi-core deployment** and shouldn't be quoted as a production
capacity claim — re-run Section 4's exact commands on real target
infrastructure (or even just a multi-core laptop) before putting an
absolute number in a resume bullet.

Rate limiting disabled (isolating raw capacity, per Section 2):

| Concurrent users | Requests/sec | Error rate | p50 | p95 | p99 |
|---:|---:|---:|---:|---:|---:|
| 10  | 25.7 req/s | 0% | 22 ms | 270 ms | 1,100 ms |
| 50  | 47.5 req/s | 0% | 480 ms | 1,700 ms | 2,500 ms |
| 150 | 45.9 req/s | 0% | 1,400 ms | 4,400 ms | 17,000 ms |

Throughput plateaus between 50 and 150 users while p99 latency grows
roughly 7x — the signature of a saturated resource, consistent with
the single-CPU-core constraint above. No errors at any tier — the
backend degrades by getting slower under this sandbox's real resource
ceiling, not by failing requests, which is the behavior you'd want to
see (assuming client-side timeouts are configured to handle it — not
verified here).

Rate limiting enabled (default), 50 users: 37.4% of `/search` requests
returned 429 — the Section 2 bug, measured before its fix was applied.

## 6. Follow-ups identified, not implemented this phase

- Re-run Section 4 on real multi-core infrastructure for numbers
  trustworthy enough to quote as a capacity claim.
- A load test with N genuinely distinct logged-in users (not one
  shared token) to actually measure the Section 2 fix's effect under
  concurrent multi-user traffic, rather than only unit-testing the key
  function in isolation.
- `SQLALCHEMY_ENGINE_OPTIONS`/connection pool size is unset anywhere
  in `app/config.py` (SQLAlchemy's defaults: `pool_size=5,
  max_overflow=10` per engine instance). Not implicated in anything
  measured this phase (zero connection-related errors even at 150
  users) — worth setting explicitly before real production concurrency
  is reached, rather than relying on the library default.
