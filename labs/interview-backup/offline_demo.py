"""Instant, dependency-free fallback for presenting synthetic data-quality cases.

NOT a live Kafka/Flink/ClickHouse demonstration. Uses the actual backup DQ
checker on deliberately generated source/target observations and emits a
standalone HTML report without Docker or third-party Python dependencies.
"""
from __future__ import annotations
import argparse
import html
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dq import evaluate

ROOT = Path(__file__).resolve().parent
SCENARIOS = ("clean", "replay", "out_of_order", "missing", "conflict", "corrupt")
BASE = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)
EXPECTED = {
    "clean": ("PASS", None),
    "replay": ("PASS", None),
    "out_of_order": ("PASS", None),
    "missing": ("FAIL", "missing_event"),
    "conflict": ("FAIL", "conflict_same_version"),
    "corrupt": ("FAIL", "payload_mismatch"),
}

def build_case(scenario: str) -> tuple[list[dict], list[dict]]:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario}")
    expected = []
    for item in json.loads((ROOT / "fixtures/trades.json").read_text()):
        row = {
            **{key: value for key, value in item.items()
               if key != "event_time_offset_seconds"},
            "run_id": "offline-" + scenario, "source_tag": "flink_sql",
            "event_time": (BASE + timedelta(
                seconds=item["event_time_offset_seconds"]
            )).isoformat(),
        }
        expected.append(row)
    if scenario == "conflict":
        extra = deepcopy(next(row for row in expected if row["event_id"] == "E02"))
        extra.update(event_id="E07", pnl="12.00")
        expected.append(extra)
    actual = deepcopy(expected)
    if scenario == "replay":
        actual.append(deepcopy(next(row for row in actual if row["event_id"] == "E02")))
    elif scenario == "out_of_order":
        older = next(row for row in actual if row["event_id"] == "E01")
        actual = [row for row in actual if row["event_id"] != "E01"] + [older]
    elif scenario == "missing":
        actual = [row for row in actual if row["event_id"] != "E03"]
    elif scenario == "corrupt":
        next(row for row in actual if row["event_id"] == "E02")["pnl"] = "999.00"
    return expected, actual

def run_cases() -> list[dict]:
    reports = []
    for scenario in SCENARIOS:
        expected, actual = build_case(scenario)
        report = evaluate("offline-" + scenario, len(expected), expected, actual)
        expected_status, rule = EXPECTED[scenario]
        actual_rules = {i["rule"] for i in report.get("issues", [])}
        if report["status"] != expected_status or (
            rule is not None and rule not in actual_rules
        ):
            raise AssertionError(f"Offline DQ result incorrect: {scenario}: {report}")
        reports.append({"scenario": scenario, "expected_physical":len(expected),
                        "actual_physical":len(actual), **report})
    return reports

def render_html(reports: list[dict]) -> str:
    rows = []
    for r in reports:
        color = "#72ddb1" if r["status"] == "PASS" else "#fa9c9c"
        issues = html.escape(json.dumps(r["issues"], sort_keys=True, ensure_ascii=False))
        dup = html.escape(json.dumps(r.get("duplicate_deliveries", {})))
        rows.append(
            "<tr><td><strong>" + html.escape(r["scenario"]) + "</strong></td>"
            + '<td style="color:' + color + '">' + html.escape(r["status"]) + "</td>"
            + "<td>" + str(r["expected_physical"]) + "</td>"
            + "<td>" + str(r["actual_physical"]) + "</td>"
            + "<td>" + str(r["observed_distinct"]) + "</td>"
            + "<td><details><summary>Evidence</summary><pre>" + issues
            + "</pre><pre>Duplicates: " + dup + "</pre></details></td></tr>"
        )
    return """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline Data QA Interview Backup</title>
<style>body{font:15px system-ui;background:#0c1424;color:#e6ecf5;max-width:1080px;
margin:auto;padding:36px}h1{font-size:30px}.note{border:1px solid #926a30;
background:#362a18;padding:16px;border-radius:10px;color:#f6d698}
table{width:100%;border-collapse:collapse;margin-top:26px}td,th{text-align:left;
padding:15px;border-bottom:1px solid #364155}th{color:#a9bad2;font-size:12px;
text-transform:uppercase}tr:hover{background:#19243a}pre{white-space:pre-wrap;
max-width:500px;color:#d0daee}details summary{cursor:pointer;color:#91c7ff}
footer{margin-top:28px;color:#8b9cb8}</style></head><body>
<div style="color:#7ad3ff;font-weight:bold;letter-spacing:2px">INTERVIEW BACKUP LAB</div>
<h1>Offline synthetic Data Quality evidence</h1>
<div class="note"><strong>SIMULATION ONLY.</strong> No Kafka, Flink, PostgreSQL or
ClickHouse was started for this HTML report. These are deterministic fixtures
evaluated by the same pure-Python DQ engine used by the live backup lab.
They cannot establish any live delivery or checkpoint guarantees.</div>
<table><thead><tr><th>Scenario</th><th>DQ</th><th>Source events</th>
<th>Physical deliveries</th><th>Unique sink IDs</th><th>Evidence</th>
</tr></thead><tbody>""" + "".join(rows) + """</tbody></table>
<footer>All events synthetic. The live dashboard uses localhost:28765.</footer>
</body></html>"""

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "artifacts" / "offline-report.html")
    args = parser.parse_args()
    reports = run_cases()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(reports), encoding="utf-8")
    args.output.with_suffix(".json").write_text(
        json.dumps(reports, indent=2, sort_keys=True), encoding="utf-8"
    )
    print("Six offline scenarios validated.")
    print(f"Open in a browser: {args.output.absolute()}")

if __name__ == "__main__":
    main()
