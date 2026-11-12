"""Shared, deliberately small PostgreSQL/Kafka/ClickHouse lab utilities."""
from __future__ import annotations

import base64
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PG_DSN = os.getenv("PG_DSN", "postgresql://qa:qa@127.0.0.1:5433/trading")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:19092")
CH_URL = os.getenv("CLICKHOUSE_URL", "http://localhost:18123").rstrip("/")
CH_USER = os.getenv("CLICKHOUSE_USER", "qa")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "qa")


def clickhouse_query(query: str, *, data: bytes = b"", params: dict[str, str] | None = None) -> str:
    """POST query and optional JSONEachRow bytes using HTTP Basic auth (lab-only)."""
    parameters = {"query": query}
    parameters.update(params or {})
    url = f"{CH_URL}/?{urlencode(parameters)}"
    token = base64.b64encode(f"{CH_USER}:{CH_PASSWORD}".encode()).decode("ascii")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={"Authorization": f"Basic {token}", "Content-Type": "text/plain; charset=utf-8"},
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def parse_json_rows(payload: str) -> list[dict]:
    return [json.loads(line) for line in payload.splitlines() if line.strip()]
