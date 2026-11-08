# Integration-test design contract

## Pretend API, real data semantics

The preparatory fake models a service with `submit(event)`, `drain()`, `source`, `target` and `reset()`. It is not a replacement for external systems; its queue allows a test to accidentally pass before processing (a deliberate trap).

## Fixture constraints to defend

- A session-scoped environment can be shared only if each test owns an isolated database/schema/topic/namespace and cleanup remains reliable.
- A function-scoped fake should not leak queue contents or emitted rows.
- Tests must assert both **that data is present** and **that invariants hold**.
- At least one setup failure and one assertion failure should demonstrate teardown behavior.
- Never assume `pytest-xdist` worker isolation merely because pytest creates a fixture per worker.
- Validate status, count and business-key identity, not only HTTP-like success.
- Do not call a fake-based test `end-to-end` when no external adapters run.

## Session deliverable

Implement the actual pytest fixtures and meaningful tests under `tests/`. The file `support/fake_pipeline.py` is supplied as test infrastructure and **not** a solved fixture architecture.
