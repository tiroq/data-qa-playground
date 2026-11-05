# Python source — intentionally incremental

This directory documents the future `src/data_qa/` Python package. It is **not yet an implemented library**. Introduce executable modules during Session 05 (comparison), Session 06 (DQ), and Session 08 (async polling), together with `pyproject.toml` and tests. Do not add fake implementations solely to populate folders.

Proposed boundaries (not installed): `data_qa.reconciliation`, `data_qa.quality`, `data_qa.polling`. Keep core comparison logic pure, use `Decimal` for money and isolate IO adapters from algorithms.

See [ROADMAP](../ROADMAP.md) and [Session 05](../exercises/05-python-live-coding/README.md).
