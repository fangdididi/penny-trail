import os
import subprocess
import sys
import unittest
from datetime import date
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import penny  # noqa: E402
from penny import Row, money  # noqa: E402

EX = os.path.join(ROOT, "examples", "lantern-tea")


def R(side, key, d, amt, ref=""):
    return Row(side, key, date(2026, 9, d), amt, ref)


class MoneyTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(money("1,234.50"), Decimal("1234.50"))
        self.assertEqual(money("(80.00)"), Decimal("-80.00"))
        self.assertEqual(money("80.00-"), Decimal("-80.00"))
        self.assertEqual(money("¥ 12"), Decimal("12.00"))
        self.assertEqual(money("-0.005"), Decimal("-0.01"))

    def test_rejects_text(self):
        with self.assertRaises(ValueError):
            money("n/a")

    def test_dates(self):
        self.assertEqual(penny.parse_day("2026-09-05T10:22:00Z"), date(2026, 9, 5))
        self.assertEqual(penny.parse_day("05.09.2026"), date(2026, 9, 5))


class RollTests(unittest.TestCase):
    def test_rolls_and_gap(self):
        rows = [R("L", 1, 1, "100"), R("L", 2, 2, "-30.10")]
        self.assertEqual(penny.roll("50", rows, "119.90")[1], Decimal("0.00"))
        self.assertEqual(penny.roll("50", rows, "120.00")[1], Decimal("0.10"))


class MatchTests(unittest.TestCase):
    def test_reference_pass_beats_date(self):
        res = penny.match([R("L", "a", 1, "-50", "INV-7")], [R("R", "b", 20, "-50", "inv7")], days=2)
        self.assertEqual(res["matches"][0]["pass"], "P1")

    def test_twins_are_not_paired(self):
        left = [R("L", "a", 3, "20"), R("L", "b", 4, "20")]
        right = [R("R", "x", 4, "20")]
        res = penny.match(left, right)
        self.assertEqual(res["matches"], [])
        self.assertEqual(len(res["twins"]), 1)

    def test_group_with_fee(self):
        left = [R("L", 1, 2, "100"), R("L", 2, 3, "50"), R("L", 3, 3, "-4.35")]
        right = [R("R", 9, 4, "145.65")]
        res = penny.match(left, right)
        self.assertEqual(res["matches"][0]["pass"], "P3")
        self.assertEqual(res["counts"]["left_only"], 0)

    def test_tolerance_only_when_asked(self):
        left = [R("L", 1, 2, "100.00")]
        right = [R("R", 1, 2, "99.70")]
        self.assertEqual(penny.match(left, right)["matches"], [])
        res = penny.match(left, right, tol_abs="0.50")
        self.assertEqual(res["matches"][0]["residual"], "-0.30")

    def test_bridge_check_is_zero(self):
        left = penny.load_csv(os.path.join(EX, "books.csv"), "L")
        right = penny.load_csv(os.path.join(EX, "bank.csv"), "R")
        res = penny.match(left, right)
        self.assertEqual(res["bridge"]["check"], "0.00")
        kinds = sorted(c["kind"] for c in res["clues"])
        self.assertEqual(kinds, ["REPEAT", "SIGN", "SWAP"])
        self.assertEqual(res["counts"]["matched"], 4)


class ClueTests(unittest.TestCase):
    def test_slide_and_late(self):
        clues = penny.find_clues([R("L", 1, 1, "45.00"), R("L", 2, 1, "70")],
                                 [R("R", 1, 2, "450.00"), R("R", 2, 25, "70")], days=3)
        kinds = sorted(c["kind"] for c in clues)
        self.assertEqual(kinds, ["LATE", "SLIDE"])

    def test_hint(self):
        lines = penny.hint("360.00")
        self.assertTrue(any("divisible by 9" in x for x in lines))
        lines = penny.hint("96.00", [R("L", 13, 18, "48.00")])
        self.assertTrue(any("L:13" in x for x in lines))


class CliTests(unittest.TestCase):
    def test_roll_cli_exit_code(self):
        cmd = [sys.executable, os.path.join(ROOT, "scripts", "penny.py"), "roll",
               os.path.join(EX, "bank.csv"), "--opening", "4200.00", "--closing", "2156.63"]
        out = subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(out.returncode, 0)
        self.assertIn("ROLLS", out.stdout)


if __name__ == "__main__":
    unittest.main()
