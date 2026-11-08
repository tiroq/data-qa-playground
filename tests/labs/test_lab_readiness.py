"""Preparation smoke only. Does NOT solve or test interview business logic."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def import_file(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_dq_fixture_and_nonempty_contract() -> None:
    payload = read_json("exercises/06-data-quality-rules/fixtures/dq_batches.json")
    assert payload["schema_version"] == 1
    batches = {c["name"]: c for c in payload["cohorts"]}
    assert len(batches) == 3
    assert len(batches["mostly_healthy"]["records"]) == 4
    assert len(batches["mixed_anomalies"]["records"]) == 10
    assert batches["empty_input"]["expected_events"] > 0
    assert not batches["empty_input"]["records"]
    mixed = batches["mixed_anomalies"]["records"]
    assert len({record["event_id"] for record in mixed}) < len(mixed)


def test_session07_fake_requires_explicit_processing() -> None:
    m = import_file("lab07_pipeline", "exercises/07-pytest-architecture/support/fake_pipeline.py")
    case = read_json("exercises/07-pytest-architecture/fixtures/api_cases.json")["cases"][0]
    fake = m.FakePipeline()
    fake.submit(case["payloads"][0])
    assert len(fake.source) == 1 and not fake.target
    assert fake.drain() == 1 and len(fake.target) == 1
    fake.reset()
    assert not fake.source and not fake.target


def test_session07_fake_processing_failure() -> None:
    m = import_file("lab07_error", "exercises/07-pytest-architecture/support/fake_pipeline.py")
    fake = m.FakePipeline(fail_processing=True)
    fake.submit({"event_id":"F1", "trade_id":"T1", "account_id":"A1"})
    with pytest.raises(RuntimeError, match="synthetic processing failure"):
        fake.drain()
    assert fake.source and not fake.target


def test_session08_manual_clock_no_real_wait() -> None:
    m = import_file("lab08_time", "exercises/08-async-testing/support/fake_time.py")

    async def run() -> None:
        clock = m.ManualClock()
        feed = m.EventuallyVisibleFeed(clock, visible_at=3.0, value={"version":2})
        assert await feed.read() is None
        await clock.sleep(2.0)
        assert await feed.read() is None
        await clock.sleep(1.0)
        assert await feed.read() == {"version":2}
        assert clock.sleeps == [2.0,1.0]

    asyncio.run(run())


def test_streaming_traces_have_observation_identity() -> None:
    folder = ROOT / "labs/streaming/scenarios"
    names = {"clean","replay","out_of_order","conflict"}
    assert {p.stem for p in folder.glob("*.jsonl")} == names
    for name in names:
        rows = [json.loads(line) for line in (folder / f"{name}.jsonl").read_text().splitlines()]
        assert [r["step"] for r in rows] == list(range(1,len(rows)+1))
        assert all(r["event_id"] and r["trade_id"] and isinstance(r["pnl"],str) for r in rows)
    replay = [json.loads(line) for line in (folder/"replay.jsonl").read_text().splitlines()]
    assert len({(r["partition"],r["offset"]) for r in replay}) < len(replay)


def test_replay_driver_does_not_deduplicate() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "labs/streaming/replay_driver.py"),
         "--scenario", "clean", "--repeat-step", "2"],
        cwd=ROOT, text=True, capture_output=True, timeout=10, check=True,
    )
    rows=[json.loads(line) for line in proc.stdout.splitlines()]
    assert len(rows)==5 and rows[1]==rows[-1]


def test_design_schema_shape() -> None:
    schema = read_json("labs/contracts/trading_event.schema.json")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["version"]["minimum"] == 1
    assert {"event_id","trade_id","account_id","version","pnl"} <= set(schema["required"])


def test_sql_labs_are_isolated() -> None:
    pg=(ROOT/"postgres/fixtures/10-sql-mock.sql").read_text()
    ch=(ROOT/"clickhouse/fixtures/09-advanced.sql").read_text()
    assert "DROP SCHEMA IF EXISTS lab10 CASCADE" in pg
    assert "DROP DATABASE IF EXISTS lab09" in ch
    assert "DROP DATABASE IF EXISTS lab03" not in ch
    assert "SELECT * FROM lab03.trade_versions" in ch


@pytest.mark.parametrize("folder", [
    "06-data-quality-rules","07-pytest-architecture","08-async-testing",
    "09-clickhouse-advanced","10-sql-mock","11-kafka-flink",
    "12-pipeline-design","13-quality-gates-ci",
])
def test_every_lab_has_russian_launch_prompt(folder: str) -> None:
    path=ROOT/"exercises"/folder/"START_HERE.md"
    assert path.is_file()
    assert "русск" in path.read_text(encoding="utf-8").lower()
