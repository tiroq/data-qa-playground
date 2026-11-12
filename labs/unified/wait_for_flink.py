"""Wait for actual RUNNING Flink job; container readiness alone is insufficient."""
from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:18081/jobs/overview")
    p.add_argument("--name", default="trade-pipeline-lab")
    p.add_argument("--timeout", type=float, default=120)
    args = p.parse_args()
    deadline = time.monotonic() + args.timeout
    last = "not queried"
    while time.monotonic() < deadline:
        try:
            with urlopen(args.url, timeout=5) as response:
                jobs = json.load(response).get("jobs", [])
            for job in jobs:
                if job.get("name") == args.name and job.get("state") == "RUNNING":
                    print(f"FLINK_JOB_RUNNING={job.get('jid')} name={args.name}")
                    return 0
            last = repr([(x.get("name"),x.get("state")) for x in jobs])
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            last = repr(exc)
        time.sleep(2)
    print(f"Flink job did not become RUNNING within {args.timeout}s: {last}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
