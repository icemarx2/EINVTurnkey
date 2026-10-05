import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from erp_bridge import checks

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
QUOTAS = [{"year_month": "11510", "track_prefix": "LP", "start_no": 50936600,
           "end_no": 50939099, "is_active": True}]


def order(num, status="SUCCESS", **kw):
    return {"einv_number": num, "einv_status": status, **kw}


class TrackCheck(unittest.TestCase):
    def test_valid_number_passes(self):
        self.assertEqual(checks.check_tracks([order("LP50936600")], QUOTAS), [])

    def test_malformed_number_flagged(self):
        self.assertEqual(len(checks.check_tracks([order("LP123")], QUOTAS)), 1)

    def test_out_of_range_flagged(self):
        self.assertEqual(len(checks.check_tracks([order("LP50939100")], QUOTAS)), 1)

    def test_unknown_prefix_flagged(self):
        self.assertEqual(len(checks.check_tracks([order("AB50936600")], QUOTAS)), 1)

    def test_inactive_quota_flagged(self):
        q = [dict(QUOTAS[0], is_active=False)]
        self.assertEqual(len(checks.check_tracks([order("LP50936600")], q)), 1)


class DuplicateCheck(unittest.TestCase):
    def test_unique_numbers(self):
        self.assertEqual(checks.check_duplicates([order("LP50936600"), order("LP50936601")]), {})

    def test_duplicate_detected(self):
        self.assertEqual(checks.check_duplicates([order("LP50936600"), order("LP50936600")]),
                         {"LP50936600": 2})


class MissingUploadCheck(unittest.TestCase):
    def test_all_confirmed(self):
        r = checks.check_missing_uploads([order("LP50936600")], NOW)
        self.assertEqual((r["issued"], r["confirmed"], r["unconfirmed"]), (1, 1, []))

    def test_stale_dispatched_flagged(self):
        sent = (NOW - timedelta(hours=3)).isoformat()
        r = checks.check_missing_uploads(
            [order("LP50936600", "DISPATCHED", einv_dispatched_at=sent)], NOW)
        self.assertEqual(r["unconfirmed"], [("LP50936600", 180)])

    def test_fresh_dispatched_not_flagged(self):
        sent = (NOW - timedelta(minutes=5)).isoformat()
        r = checks.check_missing_uploads(
            [order("LP50936600", "DISPATCHED", einv_dispatched_at=sent)], NOW)
        self.assertEqual(r["unconfirmed"], [])


class ErrorCheck(unittest.TestCase):
    def test_failed_listed(self):
        e = checks.check_errors([order("LP50936600", "FAILED", einv_result_code="E9999")])
        self.assertEqual(e[0]["code"], "E9999")

    def test_success_not_listed(self):
        self.assertEqual(checks.check_errors([order("LP50936600")]), [])


class Report(unittest.TestCase):
    def test_clean_report_ok(self):
        text, ok = checks.render_report([order("LP50936600")], QUOTAS, NOW)
        self.assertTrue(ok)
        self.assertIn("ALL CHECKS PASSED", text)

    def test_dirty_report_alerts(self):
        text, ok = checks.render_report(
            [order("LP50936600"), order("LP50936600", "FAILED")], QUOTAS, NOW)
        self.assertFalse(ok)
        self.assertIn("ATTENTION REQUIRED", text)


if __name__ == "__main__":
    unittest.main()
