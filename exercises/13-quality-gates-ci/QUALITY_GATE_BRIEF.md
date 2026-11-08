# Quality Gate Interview Requirements

The existing workflow answers only: **Can we parse fixtures and bootstrap disposable PostgreSQL?** A passing smoke check must not be interpreted as data correctness.

The candidate designs a stronger gate:

- Validate versioned source and target contracts, composite key, duplicate immutable events, same-version conflicts and Decimal fields.
- Fail when the expected cohort is unexpectedly empty (the `0 == 0` false pass).
- Compute a synthetic 95%-within-10-min SLA with an explicit eligible cohort, cutoff and denominator.
- Record business key, event ID, rule, threshold, observed count, evaluation window and code version for failing anomalies.
- Demonstrate a deliberately injected DQ fault that causes a **nonzero** exit status.
- Define blocking PR rules versus operational warning thresholds; justify false-positive avoidance.
- Fail when required tests are skipped, not collected, unexpectedly `xfail` or silently ignored.
- Diagnose transient setup errors separately; retries must not mask deterministic defects.
- Save machine-readable artifacts for a reviewer and a reproducible local command.

**Not part of preparation:** implementation of all business gate logic; Kafka/Flink end-to-end; access to proprietary or production datasets.
