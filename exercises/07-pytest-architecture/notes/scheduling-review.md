# Session 07 — Worker Scheduling Design Review

**Status:** DISCUSSED / NOT IMPLEMENTED. This note records the learner's architecture proposal and follow-up review, not a verified implementation or a completed session.

## Learner proposal (2026-11-10)

- Avoid provisioning a fresh Testcontainers stack for each of ~200 tests.
- Use a bounded pool of worker-owned test environments.
- Size the number of workers dynamically based on the selected test set rather than a fixed `-n 5`.
- Define a target capacity of roughly 50 weighted test points per worker. Example: 200 tests with 230 points lead to `ceil(230/50) = 5` requested workers.
- Mark expensive/long-running cases with higher test weights to distinguish their expected cost.
- Restrict simultaneous workers to actual machine/CI limits; if only two can run concurrently, account for batching or reduce the active pool.
- Use a unique worker identifier plus per-test identifiers to reduce collisions between datasets.
- Prefer serial test execution within a worker-owned pipeline while parallelizing across workers.

## Review: important corrections and unknowns

1. **Worker count must be selected before collection within a normal xdist invocation.** `pytest_collection_modifyitems` is too late for deciding `-n` in the controller. To use exact selected-test weights, perform a pre-collection/manifest pass or use a previous run's manifest/timing estimates in the launch wrapper. The `pytest_xdist_auto_num_workers` hook can control `-n auto` but does not, by itself, produce selected-test weights.
2. **Markers don't enforce weighted scheduling automatically.** Use a separate planner or a custom xdist scheduler. `--dist=loadgroup` and `xdist_group` enforce grouping, not weighted balancing or exclusivity of external resources.
3. **Points are only a heuristic.** Actual resource demand includes CPU, RAM, I/O, container startup, external service limits, and wall-clock durations; point targets do not guarantee an equal distribution of tests.
4. **Two-worker hardware limit means at most two live full stacks.** Do not launch five heavy environments simultaneously just because the weighted test count suggests five nominal partitions. Prefer `-n 2` or explicitly orchestrated CI batches.
5. **Worker/session fixtures are per worker process, not global.** If sharing a host/daemon or external services, make queues, topics, databases, ports, volumes and business IDs unambiguous. Include a run-specific prefix in addition to `worker_id`, which is reused across runs.
6. **Isolation and safe cleanup remain open.** Late processing after test teardown can contaminate a shared target; independent full-stack lifecycle or hard namespaces must be defended.

## Provisional design

```text
selected test manifest + marker weights + optional historical timing
    -> desired workers = ceil(total_weight / target_points)
    -> active workers = min(desired, CI CPU/RAM/service limits)
    -> one full pipeline per active worker (session scope)
    -> one dataset/business key prefix per test (function scope)
    -> xdist group scheduling when resource affinity is required
    -> teardown with diagnostics; late-write/isolation strategy still TBD
```

## Follow-up / verification to implement later

- Choose between static marker weights and observed runtime statistics.
- Prove that small selections do not allocate unnecessary workers.
- Verify actual xdist distribution under two-worker and five-worker runs.
- Demonstrate per-worker container lifecycle, concurrent dataset isolation, and teardown on failure.
- Keep Session 07 status **IN PROGRESS** until code and CI evidence exist for these properties.

References: https://pytest-xdist.readthedocs.io/en/latest/distribution.html
