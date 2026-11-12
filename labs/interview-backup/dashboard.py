"""Read-only, localhost-only visual observability for Interview Backup Lab.

No mutation endpoints and no pretense of end-to-end exactly-once. The DQ result
represents currently query-visible ClickHouse rows compared with PostgreSQL.
"""
from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import psycopg

from check import clickhouse_observations, source_manifest
from common import PG_DSN, clickhouse_query
from dq import evaluate

BASE = Path(__file__).resolve().parent
RUN_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def runs(limit: int = 30) -> list[dict]:
    with psycopg.connect(PG_DSN) as conn:
        rows = conn.execute(
            "SELECT run_id,scenario,planned_count,publication_status,created_at "
            "FROM streaming_lab.batches ORDER BY created_at DESC LIMIT %s",
            (limit,),
        ).fetchall()
    return [
        {"run_id":r[0], "scenario":r[1], "planned_count":r[2],
         "publication_status":r[3], "created_at":r[4].isoformat()}
        for r in rows
    ]


def detail(run_id: str) -> dict:
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("Invalid run ID")
    planned, source, scenario, publication = source_manifest(run_id)
    actual = clickhouse_observations(run_id)
    if publication == "PUBLISHED":
        verdict = evaluate(run_id, planned, source, actual)
    else:
        verdict = {"status":"INDETERMINATE", "issues":[
            {"rule":"publication_incomplete",
             "detail":"Producer publication is not yet sealed"}],
            "planned_count":planned,
            "observed_distinct":len({row.get("event_id") for row in actual}),
            "observed_physical":len(actual),
            "duplicate_deliveries":{}}
    target_by_event: dict[str, list[dict]] = {}
    for item in actual:
        target_by_event.setdefault(str(item.get("event_id")), []).append(item)
    rows = []
    for expected in sorted(source, key=lambda row: row["event_id"]):
        seen = target_by_event.pop(expected["event_id"], [])
        rows.append({
            "event_id":expected["event_id"], "account_id":expected["account_id"],
            "trade_id":expected["trade_id"], "version":expected["version"],
            "expected_pnl":expected["pnl"], "actual_pnls":[r.get("pnl") for r in seen],
            "deliveries":len(seen),
            "presence":"VISIBLE" if seen else "MISSING",
        })
    for event_id, seen in sorted(target_by_event.items()):
        rows.append({
            "event_id":event_id, "account_id":seen[0].get("account_id"),
            "trade_id":seen[0].get("trade_id"),"version":seen[0].get("version"),
            "expected_pnl":None,"actual_pnls":[r.get("pnl") for r in seen],
            "deliveries":len(seen),"presence":"UNEXPECTED",
        })
    return {
        "run_id":run_id,"scenario":scenario,
        "publication_status":publication,
        "result":verdict,"events":rows,
        "caveat":"Observed snapshot only; no atomic Kafka-to-ClickHouse completion proof.",
    }


def check_health() -> dict:
    db = ch = False
    try:
        with psycopg.connect(PG_DSN, connect_timeout=3) as conn:
            db = conn.execute("SELECT 1").fetchone()[0] == 1
    except Exception:
        pass
    try:
        ch = clickhouse_query("SELECT 1").strip() == "1"
    except Exception:
        pass
    return {"ready":db and ch,"postgres":db,"clickhouse":ch,
            "pipeline":"See Flink UI; HTTP readiness does not prove job running"}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, value: dict | list, status: int = 200) -> None:
        body = json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path in ("/","/index.html"):
                body = (BASE / "dashboard.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type","text/html; charset=utf-8")
                self.send_header("Cache-Control","no-store")
                self.send_header("Content-Length",str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == "/api/health":
                health = check_health()
                self.send_json(health, 200 if health["ready"] else 503)
            elif parsed.path == "/api/runs":
                self.send_json(runs())
            elif parsed.path == "/api/run":
                run_id = parse_qs(parsed.query).get("run_id",[""])[0]
                self.send_json(detail(run_id))
            else:
                self.send_json({"error":"not found"},404)
        except ValueError as exc:
            self.send_json({"error":str(exc)},400)
        except Exception as exc:
            self.log_error("Read-only dashboard query failed: %s",exc)
            self.send_json({"error":f"Data temporarily unavailable: {type(exc).__name__}"},503)


if __name__ == "__main__":
    print("Interview Backup Dashboard on 0.0.0.0:8765 (host localhost:28765)",flush=True)
    ThreadingHTTPServer(("0.0.0.0",8765),Handler).serve_forever()
