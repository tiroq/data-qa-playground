"""Small, real HTTP teaching service: 202 -> worker -> PostgreSQL -> ClickHouse.

This is a deliberately controlled local fixture, not the Exness API and not a
Kafka consumer. The completion signal means a terminal processing outcome
after the sink-write attempt; it is independent of reconciliation correctness.
"""
from __future__ import annotations

import json
import threading
import time
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Queue
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg
from clickhouse_driver import Client


class LabAPI:
    def __init__(self, postgres_dsn: str, clickhouse_dsn: str, database: str):
        self._pg = postgres_dsn
        self._ch = clickhouse_dsn
        self._db = database
        self._queue: Queue[dict | None] = Queue()
        self._gate = threading.Event()
        self._gate.set()
        self._condition = threading.Condition()
        self._completed: dict[str, str] = {}
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._make_handler())
        self._http = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._worker = threading.Thread(target=self._consume, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_port}/trades"

    def _make_handler(self):
        queue = self._queue

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                if self.path != "/trades":
                    self.send_error(404)
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 0 < size < 100_000:
                        raise ValueError("Invalid body length")
                    payload = json.loads(self.rfile.read(size))
                    for key in ("trade_id", "account_id", "version", "pnl", "status"):
                        if key not in payload:
                            raise ValueError(f"Missing {key}")
                    if not payload["trade_id"] or not payload["account_id"]:
                        raise ValueError("Missing business key")
                    event_id = payload.get("event_id") or f"E-{uuid4().hex}"
                    if not isinstance(event_id, str) or not event_id:
                        raise ValueError("Bad event_id")
                    fault = payload.get("_lab_fault")
                    if fault not in (None, "skip_sink", "duplicate_sink", "corrupt_sink"):
                        raise ValueError("Unknown lab fault")
                    item = dict(payload, event_id=event_id)
                    int(item["version"])
                    Decimal(str(item["pnl"]))
                except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                    self.send_error(400, str(error))
                    return
                queue.put(item)  # Acceptance precedes durable processing.
                reply = json.dumps({"event_id": event_id, "trade_id": item["trade_id"]}).encode()
                self.send_response(202)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)

        return Handler

    def pause_worker(self) -> None:
        self._gate.clear()

    def resume_worker(self) -> None:
        self._gate.set()

    def __enter__(self):
        self._http.start()
        self._worker.start()
        return self

    def __exit__(self, *args):
        self.resume_worker()
        self._queue.put(None)
        self._worker.join(timeout=15)
        self._server.shutdown()
        self._server.server_close()
        self._http.join(timeout=5)
        if self._worker.is_alive():
            raise RuntimeError("Test lab worker failed to stop before DB teardown")

    def _consume(self):
        ch = Client.from_url(self._ch)
        try:
            while True:
                item = self._queue.get()
                if item is None:
                    self._queue.task_done()
                    return
                self._gate.wait()
                outcome = "stored"
                try:
                    with psycopg.connect(self._pg) as pg:
                        pg.execute(
                            """
                            INSERT INTO lab07.trade_events
                                (event_id, trade_id, account_id, version, pnl, status)
                            VALUES (%(event_id)s, %(trade_id)s, %(account_id)s,
                                    %(version)s, %(pnl)s, %(status)s)
                            """,
                            item,
                        )
                    if item.get("_lab_fault") == "skip_sink":
                        outcome = "skipped"
                    else:
                        value = Decimal(str(item["pnl"]))
                        if item.get("_lab_fault") == "corrupt_sink":
                            value += Decimal("1.00")
                        row = (item["event_id"], item["trade_id"], item["account_id"],
                               int(item["version"]), value, item["status"])
                        repeats = 2 if item.get("_lab_fault") == "duplicate_sink" else 1
                        ch.execute(
                            f"INSERT INTO {self._db}.trade_events_raw "
                            "(event_id, trade_id, account_id, version, pnl, status) VALUES",
                            [row] * repeats,
                        )
                except Exception as exc:
                    outcome = f"error: {type(exc).__name__}: {exc}"
                finally:
                    with self._condition:
                        self._completed[item["event_id"]] = outcome
                        self._condition.notify_all()
                    self._queue.task_done()
        finally:
            ch.disconnect()

    def post(self, payload: dict) -> tuple[int, dict]:
        body = json.dumps(payload).encode()
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())

    def wait_completed(self, event_ids, *, timeout=10.0) -> dict[str, str]:
        """Bounded terminal state barrier, not a Kafka offset or DQ assertion."""
        deadline = time.monotonic() + timeout
        expected = set(event_ids)
        if not expected:
            raise ValueError("An empty batch must explicitly bypass the barrier")
        with self._condition:
            while not expected.issubset(self._completed):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    pending = expected - self._completed.keys()
                    raise TimeoutError(f"Processing barrier timed out: pending={pending}")
                self._condition.wait(timeout=remaining)
            return {event_id: self._completed[event_id] for event_id in expected}
