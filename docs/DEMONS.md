# DEMONS

> Catalog of known-risky decisions, deferred fixes, and architectural debt in
> arq-research. Each entry is tagged with the code site (when localized) or
> the affected subsystem (when architectural). Inline `# DEMON:` comments
> near the source point back to this document.
>
> **Conventions:**
> - **WHERE** — file path + line range, or "ARCH" if architectural
> - **WHY IT EXISTS** — the constraint that produced it
> - **WHEN TO FIX** — the concrete trigger to revisit
> - **HOW TO FIX** — the path of least surprise
>
> Add new demons when you make a deliberate trade-off the next developer
> wouldn't expect. Delete them when you fix the underlying issue.

---

## Observation pipeline (GBIF on-demand fetch)

### 1. The SOURCE column is the contract — keep it in sync everywhere

**WHERE:**
- `kg/loaders/observations.py:50-52` (DataSource registrations)
- `kg/loaders/observations.py:115-129` (Observation.source routing)
- `webapp/backend/gbif.py:_normalize_to_stg` (writes `SOURCE='gbif'`)
- `dbt/models/staging/stg_observations.py` (writes `source='inat'|'arborphy'`)
- `scripts/upload_stg_observations.py:117-127` (backfill + delete-by-source)

**WHY IT EXISTS:** RAI's `Observation.source` predicate is populated by
matching the `SOURCE` column against `where(...SOURCE == X)` clauses.
Trail-observation queries filter by `Observation.source(obs, datasource)`.
An observation with a `SOURCE` value that has no matching `DataSource.new()`
and no matching `where(...).define(Observation.source(...))` block is
silently invisible to those queries.

**WHEN TO FIX:** Whenever you add a new ingestion path (e.g. "mobile-direct,"
"chatbot-import"), or a new SOURCE value.

**HOW TO FIX:** Add three things in lockstep:
1. The new value writes to `SOURCE` (in the ingester)
2. `define(DataSource.new(name=<value>))` in `kg/loaders/observations.py`
3. `where(... SOURCE == <value>).define(Observation.source(...))` block
   in the same file

Eventually consolidate into a single dict literal that drives all three.

---

### 2. DELETE-then-INSERT is now transactional, but partial INSERT-success isn't covered

**WHERE:** `webapp/backend/snowflake_upload.py:upload_observations`

**WHY IT EXISTS:** We disabled autocommit and wrap DELETE + write_pandas in
a single transaction. If `write_pandas` returns `success=False` or raises,
the transaction is rolled back. However: `write_pandas` does PUT + COPY
INTO under the hood and may report partial success (some rows inserted,
some rejected). We treat any non-OK return as a full rollback, which is
the safe choice — but it means **a single bad GBIF record fails the
entire batch**, including the otherwise-valid rows.

**WHEN TO FIX:** When you see legitimate fetches failing because one record
has a malformed field. (You'll know because the cid in the 500 response
will let you find the offending row in logs.)

**HOW TO FIX:** Pre-validate each row against the target schema before
upload; drop bad rows with a warning rather than failing the batch.
Alternatively, use `MERGE INTO` with `ON_ERROR='CONTINUE'`.

---

### 3. Schema definition for `stg_observations` lives in three places

**WHERE:**
1. `dbt/models/staging/stg_observations.py::COLS` + `H3_RESOLUTIONS`
   (the canonical schema for the bulk iNat load)
2. The Snowflake DDL (created out-of-band — there's no committed CREATE
   TABLE in this repo besides `script/gbif_observation.sql` for a
   different table)
3. `webapp/backend/gbif.py::_empty_df` + `_normalize_to_stg` (the on-demand
   path's column list)
4. `kg/loaders/observations.py::obs_table = m.Table(... schema=...)`
   (RAI's view of the columns and their types)

**WHY IT EXISTS:** Three independent code paths populate the table and one
binds it to RAI. Each was written at a different time.

**WHEN TO FIX:** First time you have to add or rename a column. (Or when
the RAI loader silently sees null in a new column.)

**HOW TO FIX:** Promote `dbt/models/staging/stg_observations.py::COLS` to
a shared constant (already importable as
`from dbt.models.staging.stg_observations import COLS, H3_RESOLUTIONS`
— see `scripts/upload_stg_observations.py:35`). Have `_empty_df` and the
RAI loader's `schema={...}` derive from it.

---

### 4. `quality_grade` semantics collide between iNat and GBIF

**WHERE:** `webapp/backend/gbif.py::_quality_from_basis`

**WHY IT EXISTS:** iNat's `QUALITY_GRADE='research'` means "photo + GPS +
date + ≥2/3 community ID agreement." GBIF's `basisOfRecord` is a coarser
descriptor (HUMAN_OBSERVATION, MACHINE_OBSERVATION, etc.). The current
mapping calls any HUMAN_OBSERVATION "research," which conflates verified
and unverified records.

**WHEN TO FIX:** Before any product filter ("show only research-grade
observations") goes live in the UI.

**HOW TO FIX:** Either:
- Always emit `quality_grade='casual'` for GBIF rows (safest)
- Map from GBIF's `identificationVerificationStatus` or check that the
  record's `issues` list is empty before promoting to "research"
- Introduce a new value like `gbif_observation` so the iNat semantics
  remain pure

---

## Cache layer (TTL in-process)

### 5. Cache is unbounded

**WHERE:** `webapp/backend/cache.py::_STORE`

**WHY IT EXISTS:** Stdlib-only constraint + early dev. No new dependencies.

**WHEN TO FIX:** First sign of memory growth in `cache_stats()` (the
endpoint at `/api/observations/cache/stats` reports entry count).

**HOW TO FIX:**
- Cap with `collections.OrderedDict.move_to_end` for LRU eviction
- Or add a periodic sweep that drops `expires_at <= now` on every Nth
  insertion
- Or just call `cache_bust()` on a timer (cron-style background task)

---

### 6. No single-flight on cache miss (thundering herd)

**WHERE:** `webapp/backend/cache.py::ttl_cache::wrapper`

**WHY IT EXISTS:** Deliberate choice. Computing inside the lock would
serialize all RAI queries through one thread, defeating the cache's
latency benefit. The downside is that on a cold key, N parallel callers
each issue their own Snowflake query.

**WHEN TO FIX:** When you see Snowflake query-count spike on
`cache_bust()` calls, or when a single hot key (e.g. the home page's
`species_co_occurrence_graph()`) starts dominating warehouse credit
consumption.

**HOW TO FIX:** Track an in-flight set `dict[key, threading.Event]`. On
miss, if another thread already has the key, wait on its Event; first
thread computes, populates store, calls `event.set()`.

---

### 7. `df.copy()` on every hit

**WHERE:** `webapp/backend/cache.py::ttl_cache::wrapper` (the value-return
paths)

**WHY IT EXISTS:** Defensive — prevents a caller from mutating
(`.rename()`, `.fillna()`) the cached DataFrame and poisoning subsequent
reads. Many of the router endpoints DO mutate the returned frame.

**WHEN TO FIX:** When cache-hit latency starts being noticeable (the
docstring claims hits are fast; with large frames they're not).

**HOW TO FIX:**
1. Audit every consumer of cached query results, switch to non-mutating
   patterns (or wrap mutations in a copy at the call site)
2. Switch this module to return frames as-is and document immutability
3. Or adopt pandas 2.x copy-on-write mode globally

---

### 8. Cache namespace bust may miss observation-dependent queries in `"ref"`

**WHERE:** `webapp/backend/routers/observations.py::OBSERVATION_DEPENDENT_NAMESPACES`

**WHY IT EXISTS:** Most ref-data queries (Newcomb, ecosites) are over
static data, so they live in the `"ref"` namespace with a 1-hour TTL.
But a couple of queries — notably `kg/queries/predicates.py::predicate_graph`
— are technically observation-dependent (Species entities are auto-created
from observation rows). They got assigned `"ref"` because their dominant
cost is the cross-concept graph traversal, not the join with observations.
A `/fetch-area` upload won't bust them.

**WHEN TO FIX:** When a user reports "I uploaded new observations but the
predicate graph still doesn't show the new species" — they'd have to wait
up to 10 minutes for the cache to expire.

**HOW TO FIX:**
- Easiest: append `"ref"` to `OBSERVATION_DEPENDENT_NAMESPACES`
- Cleaner: split `"ref"` into `"ref_static"` (Newcomb, ecosites) and
  `"ref_observation_derived"` (predicates) and bust only the latter

---

## Architecture

### 9. `kg/queries/*` depends on `webapp/backend/cache` (layer inversion)

**WHERE:** ARCH — affects all of `kg/queries/`

**WHY IT EXISTS:** The cache decorator was the simplest way to memoize
RAI query results, and the decorator's natural home was next to the
HTTP layer.

**WHEN TO FIX:** First time someone tries to use the `kg/` package
standalone (CLI script, batch job, notebook) and gets `ImportError` on
`webapp.backend.cache`.

**HOW TO FIX:** Move `webapp/backend/cache.py` to `kg/cache.py` (or a
neutral `arq_common/`). Re-export from `webapp/backend/cache.py` for
backward compat:
```python
# webapp/backend/cache.py
from kg.cache import ttl_cache, cache_bust, cache_stats  # noqa: F401
```

---

### 10. `POST /api/observations/fetch-area` is sync & blocking

**WHERE:** `webapp/backend/routers/observations.py::fetch_area`

**WHY IT EXISTS:** Sync `def` is the simplest FastAPI pattern. A
single-developer dev environment can tolerate multi-second blocks.

**WHEN TO FIX:** When a second developer or a UI starts hitting this
concurrently. Starlette's default 40-thread pool means ~5 concurrent
fetches saturate everything.

**HOW TO FIX:** Three increments:
1. (Easy) Add `from fastapi import BackgroundTasks` — kick off the GBIF
   fetch + Snowflake upload in a background task and return `{cid, status:
   'started'}`. Add a `GET /api/observations/fetch-status/{cid}` to
   poll.
2. (Medium) Move to a real job queue (RQ, Celery, or a Snowflake-task
   approach).
3. (Bigger) Convert to `async def` with `httpx.AsyncClient` for GBIF
   pagination and a thread offload for the Snowflake driver (which is
   sync).

---

### 11. No authentication on the mutation endpoint

**WHERE:** `webapp/backend/routers/observations.py::fetch_area`,
`webapp/backend/routers/observations.py::cache_bust_endpoint`

**WHY IT EXISTS:** Localhost-only CORS feels like enough for a single-dev
setup. It isn't — CORS only protects browser callers.

**WHEN TO FIX:** Before this server is reachable on any non-loopback
address (Tailscale, ngrok, deployment, anything).

**HOW TO FIX:** Add an API key check via FastAPI's `Depends(api_key_header)`
or restrict the router to a separate internal-admin port that's
firewalled off.

---

### 12. Hardcoded production Snowflake target

**WHERE:** `webapp/backend/snowflake_upload.py:ACCOUNT-TABLE`,
`scripts/upload_stg_observations.py:ACCOUNT-TABLE` (same constants,
copy-pasted)

**WHY IT EXISTS:** There's only one Snowflake environment today.

**WHEN TO FIX:** As soon as a staging environment exists, or when a
contributor's machine needs to NOT write to prod.

**HOW TO FIX:** Read from environment with refuse-by-default-on-prod:
```python
ACCOUNT  = os.environ["ARQ_SNOWFLAKE_ACCOUNT"]
TABLE    = os.environ.get("ARQ_STG_OBSERVATIONS_TABLE", "stg_observations_dev")
# Refuse to write to the prod table unless explicitly opted in
if TABLE == "stg_observations" and os.environ.get("ARQ_ENV") != "prod":
    raise RuntimeError("Refusing to write to production stg_observations from non-prod env")
```

---

### 13. GBIF pagination is sequential

**WHERE:** `webapp/backend/gbif.py::_iter_occurrences`

**WHY IT EXISTS:** The simplest possible HTTP pagination loop. For
typical quest areas (a single park, a few hundred observations) it's
fast enough.

**WHEN TO FIX:** When a fetch takes >30s end-to-end (you'll see it in
the correlation-ID logs).

**HOW TO FIX:**
1. Reuse a `requests.Session` for keep-alive (avoids TLS handshake per
   page).
2. Fetch the total count from the first page's `count` field, then
   parallelize remaining offsets with a `ThreadPoolExecutor` (4–8 workers
   is fine; GBIF rate-limits at much higher concurrency).
3. Add an overall wall-clock budget so a slow GBIF day can't hang the
   server forever.

---

### 14. Snowflake connection is opened per-call

**WHERE:** `webapp/backend/snowflake_upload.py::upload_observations`

**WHY IT EXISTS:** Simplicity. One call per `/fetch-area` request.

**WHEN TO FIX:** When you see auth handshakes (~500ms-2s each) dominating
the upload time. Or when you start running multiple uploads per minute.

**HOW TO FIX:** Module-level singleton connection guarded by a lock,
with reconnect on `OperationalError`. (Don't use a thread pool — the
connection is what holds the transaction; one transaction per request
means one connection per request.) Better: cache the PAT (read once at
module init).

---

## How to add a new demon

When you make a deliberate trade-off that the next developer wouldn't
expect from reading the code:

1. Add an inline `# DEMON: <short summary>` comment at the source.
2. Add a numbered entry here with WHERE / WHY / WHEN / HOW.
3. If you're fixing a demon, delete the entry AND the inline comment.

This document is the contract that "I knew about this" doesn't end up as
tribal knowledge.
