"""Offline negative controls: no Docker, Kafka or database required."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dq import evaluate

TIME = "2026-11-12T12:00:00+00:00"


def ev(id="E1", trade="T1", version=1, pnl="1.00", status="FILLED"):
    return {"run_id":"r1","event_id":id,"trade_id":trade,"account_id":"A1",
            "version":version,"pnl":pnl,"status":status,"event_time":TIME,"source_tag":"flink_sql"}


class DqChecks(unittest.TestCase):
    def test_exact_payload_and_decimal_scale_pass(self):
        source=[ev()]
        target=[{**ev(), "pnl":"1.0000"}]
        self.assertEqual(evaluate("r1",1,source,target)["status"],"PASS")

    def test_replay_does_not_hide_or_double_count_business_event(self):
        source=[ev("E1"),ev("E2",trade="T2")]
        rows=[ev("E1"),ev("E1")]
        result=evaluate("r1",2,source,rows)
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual(result["duplicate_deliveries"],{"E1":1})
        self.assertIn("missing_event", {i["rule"] for i in result["issues"]})

    def test_same_version_conflict_before_latest_selection(self):
        source=[ev("E1",pnl="1"),ev("E2",pnl="2")]
        result=evaluate("r1",2,source,source)
        self.assertIn("conflict_same_version", {i["rule"] for i in result["issues"]})

    def test_different_versions_are_not_conflicting(self):
        source=[ev("E1",version=1,pnl="1"),ev("E2",version=2,pnl="2")]
        self.assertEqual(evaluate("r1",2,source,source)["status"],"PASS")

    def test_same_event_corrupted_payload(self):
        source=[ev()]
        actual=[ev(pnl="999")]
        self.assertIn("payload_mismatch",{i["rule"] for i in evaluate("r1",1,source,actual)["issues"]})

    def test_identical_replay_is_not_business_failure(self):
        e=ev()
        result=evaluate("r1",1,[e],[e,e])
        self.assertEqual(result["status"],"PASS")
        self.assertEqual(result["duplicate_deliveries"],{"E1":1})

    def test_unexpected_empty_is_setup_error(self):
        self.assertEqual(evaluate("r1",0,[],[])["status"],"ERROR")
        self.assertEqual(evaluate("r1",2,[],[])["status"],"ERROR")

    def test_distinct_counts_can_hide_wrong_ids(self):
        result=evaluate("r1",2,[ev("E1"),ev("E2",trade="T2")],
                        [ev("E1"),ev("E9",trade="T9")])
        self.assertEqual(result["status"],"FAIL")
        self.assertEqual({i["rule"] for i in result["issues"]},
                         {"missing_event","unexpected_event"})

    def test_unsealed_source_is_not_misclassified_as_missing(self):
        source=[ev("E1")]
        result=evaluate("r1",1,source,[],sealed=False)
        self.assertEqual(result["status"],"INDETERMINATE")
        self.assertEqual([i["rule"] for i in result["issues"]],["source_batch_unsealed"])
        self.assertEqual(evaluate("r1",1,source,[],sealed=True)["status"],"FAIL")

    def test_trade_versions_must_remain_on_one_output_partition(self):
        source=[ev("E1",version=1),ev("E2",version=2,pnl="2")]
        same=[{**e,"kafka_partition":0} for e in source]
        self.assertEqual(evaluate("r1",2,source,same)["status"],"PASS")
        different=[{**same[0]},{**same[1],"kafka_partition":1}]
        result=evaluate("r1",2,source,different)
        self.assertIn("cross_partition_trade",{i["rule"] for i in result["issues"]})

    def test_wrong_flink_tag_fails(self):
        result=evaluate("r1",1,[ev()],[{**ev(),"source_tag":"direct_insert"}])
        self.assertIn("invalid_source_tag",{i["rule"] for i in result["issues"]})


if __name__ == "__main__":
    unittest.main()
