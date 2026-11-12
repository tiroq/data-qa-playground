"""Offline checks for interview backup, no Docker or third-party libs."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from offline_demo import EXPECTED, SCENARIOS, build_case, render_html, run_cases
from dq import evaluate

class BackupOfflineTests(unittest.TestCase):
    def test_all_cases_validate_expected_quality(self):
        reports=run_cases()
        self.assertEqual({r["scenario"] for r in reports},set(SCENARIOS))
        for r in reports:
            self.assertEqual(r["status"],EXPECTED[r["scenario"]][0])

    def test_replay_is_physical_only(self):
        source,actual=build_case("replay")
        self.assertEqual(len(actual),len(source)+1)
        report=evaluate("offline-replay",len(source),source,actual)
        self.assertEqual(report["status"],"PASS")
        self.assertIn("E02",report["duplicate_deliveries"])

    def test_missing_and_corrupt_falsify_identity_or_payload(self):
        for scenario,rule in (("missing","missing_event"),("corrupt","payload_mismatch")):
            source,actual=build_case(scenario)
            report=evaluate("offline-"+scenario,len(source),source,actual)
            self.assertEqual(report["status"],"FAIL")
            self.assertIn(rule,{x["rule"] for x in report["issues"]})

    def test_static_html_discloses_offline_origin(self):
        content=render_html(run_cases())
        self.assertIn("SIMULATION ONLY",content)
        self.assertIn("No Kafka, Flink, PostgreSQL",content)

    def test_source_publication_and_key_contract_are_explicit(self):
        root=Path(__file__).resolve().parents[1]
        self.assertIn("publication_status",(root/"sql/postgres.sql").read_text())
        sql=(root/"flink/pipeline.sql").read_text()
        self.assertIn("'key.fields' = 'business_key'",sql)
        self.assertIn("'value.fields-include' = 'EXCEPT_KEY'",sql)
        sink=(root/"sink.py").read_text()
        self.assertIn("committed = consumer.commit(asynchronous=False)",sink)
        self.assertIn('getattr(p, "err", None)',sink)

if __name__=="__main__":
    unittest.main()
