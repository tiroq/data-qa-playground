# Async testing cases

The supplied fake is a deterministic analogue of delayed query visibility, **not** Kafka or a real database.

| Case | Input | Expected requirement |
|---|---|---|
| Eventual success | Record becomes visible at t=3s | Return the record before a t=5s deadline |
| Deadline exceeded | Record becomes visible at t=9s; deadline t=4s | Raise documented timeout with last observation |
| Transient IO error | First read raises; second succeeds | Either retry explicitly specified exceptions or propagate per declared policy |
| Immediate success | Visible at t=0s | Do not sleep unnecessarily |
| Zero/negative interval | interval <= 0 | Reject invalid configuration |
| Invalid timeout | timeout <= 0 | Define validation policy and test it |
| Cancellation | Task cancelled while waiting | Do not convert cancellation into an ordinary timeout |
| Stale observation | Record visible but below expected version | Predicate must reject it; do not succeed on mere presence |

## Boundaries

- Inject `clock.monotonic` and `clock.sleep`; avoid mocking global time when not required.
- Never assume one poll corresponds to one event or one database transaction.
- Keep retries **read-only**; a repeated write can produce duplicate events.
- Define whether an exception should be included in timeout diagnostics and whether last good observation is retained.

## Exercise output

The learner writes `wait_until`, tests and a comparison between bounded polling, exponential backoff and event-driven subscription. Prebuilt support contains no answer algorithm.
