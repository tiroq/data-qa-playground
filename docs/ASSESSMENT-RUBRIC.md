# QA Data Stack Interview Assessment Rubric

Assess **observed evidence**, not perceived fluency. The learner's discussion and all interview practice are in Russian.

| Dimension | Weight | Evidence |
|---|---:|---|
| Functional correctness | 35% | Correct keys, joins, filters, aggregates, versions and outputs |
| Edge cases / DQ reasoning | 25% | NULL, duplicate delivery, source duplication, late events, SLA denominators |
| Testing and reproducibility | 20% | Isolation, meaningful assertions, verification evidence, non-vacuous pass |
| Design trade-offs and efficiency | 10% | Complexity, time and memory, ClickHouse/Kafka failure boundaries |
| Communication and completeness | 10% | Assumptions stated, required columns returned, Russian-language explanation |

**Score:** 0–10 with short supporting observations; not a statistical measure. At the end of each session record 3 concrete improvement targets.

**Session 01 baseline (informal):** strong composite keys and reconciliation fundamentals; watch GROUP BY on status (splits a business key), omitted required flags, join multiplication and correctness under timing constraints. This is a learning observation, not a formal certification.

**No-empty-PASS:** a test or data quality rule that evaluates zero rows must explicitly decide whether that cohort is valid; otherwise fail with a diagnostic. A successful command exit code does not alone prove data correctness.

## Mock-specific checks

- Time-box the original solution; no hints while under mock conditions.
- Score correctness and **completeness of required output** separately.
- Record a representative bad assumption and a reproducible counterexample.
- Separate untested topics from failed topics.
