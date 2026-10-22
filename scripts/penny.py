#!/usr/bin/env python3
"""penny.py - helper for the Penny Trail skill.

Read-only. Standard library only (Python 3.8+). Money is handled with
Decimal, never float.

Commands
  roll   prove one side is complete: opening + movements == closing
  match  pair two CSV records in strict-to-loose passes and list what is left
  hint   read the fingerprint of an unexplained difference

CSV input needs a date column and an amount column. Optional columns:
id, ref, desc, party. Column names are matched case-insensitively, and the
common aliases below are accepted.
"""
import argparse
import csv
import itertools
import json
import re
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")
ALIASES = {
    "date": ["date", "day", "posted", "posting date", "value date", "booking date", "日期", "交易日期"],
    "amount": ["amount", "amt", "value", "sum", "金额", "交易金额"],
    "id": ["id", "line", "no", "row", "编号", "序号"],
    "ref": ["ref", "reference", "invoice", "order", "check", "cheque", "参考号", "单号"],
    "desc": ["desc", "description", "memo", "narrative", "details", "摘要", "备注"],
    "party": ["party", "payee", "payer", "counterparty", "vendor", "customer", "对方", "交易对方"],
}
DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d", "%d.%m.%Y"]


# ---------------------------------------------------------------- parsing

def money(text):
    """Parse a money string into a Decimal rounded to cents.

    Accepts thousands separators, currency marks, (1,234.50) and 1234.50-
    as negatives. Raises ValueError on anything else.
    """
    if isinstance(text, Decimal):
        return text.quantize(CENT, rounding=ROUND_HALF_UP)
    s = str(text).strip()
    if not s:
        raise ValueError("empty amount")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.endswith("-"):
        neg, s = True, s[:-1]
    s = re.sub(r"[\s,'_]|[A-Za-z$€£¥￥]", "", s)
    if s.startswith("-"):
        neg, s = (not neg), s[1:]
    elif s.startswith("+"):
        s = s[1:]
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError("not an amount: %r" % text)
    if neg:
        d = -d
    return d.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_day(text):
    s = str(text).strip()
    if len(s) > 10 and s[4:5] in "-/.":
        s = s[:10]  # drop a time part such as 2026-09-05T10:00 or 2026-09-05 10:00
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError("unknown date format: %r" % text)


def norm_ref(text):
    return re.sub(r"[^0-9a-z]", "", str(text or "").lower())


class Row(object):
    __slots__ = ("side", "key", "day", "amount", "ref", "desc", "party")

    def __init__(self, side, key, day, amount, ref="", desc="", party=""):
        self.side, self.key, self.day = side, str(key), day
        self.amount = money(amount)
        self.ref, self.desc, self.party = ref or "", desc or "", party or ""

    def label(self):
        return "%s:%s" % (self.side, self.key)

    def as_dict(self):
        return {"side": self.side, "key": self.key, "date": self.day.isoformat(),
                "amount": str(self.amount), "ref": self.ref, "desc": self.desc}


def _pick(fieldnames, wanted):
    low = {f.strip().lower(): f for f in fieldnames if f}
    for alias in ALIASES[wanted]:
        if alias in low:
            return low[alias]
    return None


def load_csv(path, side, flip=False):
    """Load a CSV into Rows. flip=True reverses the sign of every amount."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {k: _pick(reader.fieldnames or [], k) for k in ALIASES}
        if not cols["date"] or not cols["amount"]:
            raise ValueError("%s: need a date column and an amount column, got %s"
                             % (path, reader.fieldnames))
        for n, rec in enumerate(reader, start=1):
            if not (rec.get(cols["amount"]) or "").strip():
                continue
            amt = money(rec[cols["amount"]])
            if flip:
                amt = -amt
            key = rec.get(cols["id"]) if cols["id"] else None
            rows.append(Row(side, key or n, parse_day(rec[cols["date"]]), amt,
                            rec.get(cols["ref"], "") if cols["ref"] else "",
                            rec.get(cols["desc"], "") if cols["desc"] else "",
                            rec.get(cols["party"], "") if cols["party"] else ""))
    return rows


# ---------------------------------------------------------------- roll

def roll(opening, rows, closing):
    """Return (computed_closing, gap). gap == 0 means the population rolls."""
    opening, closing = money(opening), money(closing)
    computed = opening + sum((r.amount for r in rows), Decimal("0"))
    return computed, closing - computed


# ---------------------------------------------------------------- match

def _within(a, b, days):
    return abs((a.day - b.day).days) <= days


def _tolerance(amount, tol_abs, tol_pct):
    return max(money(tol_abs), (abs(amount) * Decimal(str(tol_pct)) / 100).quantize(CENT))


def match(left, right, days=3, tol_abs="0", tol_pct="0", group_max=4, group_pool=18):
    """Pair rows from two sides. Returns a dict with matches, twins, leftovers.

    Passes, strictest first:
      P1 same reference and same amount
      P2 same amount, dates inside the window, exactly one candidate each way
      P3 one row equals the exact sum of 2..group_max rows on the other side
      P4 amounts inside tolerance, dates inside the window, one candidate
    A row with more than one equally good candidate is never paired; it is
    reported as a twin so a person decides.
    """
    open_l = list(left)
    open_r = list(right)
    matches, twins = [], []

    def close(pass_name, ls, rs, note=""):
        for x in ls:
            open_l.remove(x)
        for y in rs:
            open_r.remove(y)
        lsum = sum((x.amount for x in ls), Decimal("0"))
        rsum = sum((y.amount for y in rs), Decimal("0"))
        matches.append({"pass": pass_name, "left": [x.key for x in ls],
                        "right": [y.key for y in rs], "left_sum": str(lsum),
                        "right_sum": str(rsum), "residual": str(rsum - lsum), "note": note})

    # P1 reference + amount
    for x in list(open_l):
        if x not in open_l or not norm_ref(x.ref):
            continue
        cands = [y for y in open_r if norm_ref(y.ref) == norm_ref(x.ref) and y.amount == x.amount]
        if len(cands) == 1:
            back = [z for z in open_l if norm_ref(z.ref) == norm_ref(x.ref) and z.amount == x.amount]
            if len(back) == 1:
                close("P1", [x], cands, "same ref")

    # P2 exact amount within date window, unique both ways
    seen_twin = set()
    for x in list(open_l):
        if x not in open_l:
            continue
        cands = [y for y in open_r if y.amount == x.amount and _within(x, y, days)]
        if not cands:
            continue
        back = [z for z in open_l if z.amount == cands[0].amount and _within(z, cands[0], days)]
        if len(cands) == 1 and len(back) == 1:
            close("P2", [x], cands, "%+d days" % (cands[0].day - x.day).days)
        else:
            group = tuple(sorted(set(z.label() for z in back + [x] + cands)))
            if group not in seen_twin:
                seen_twin.add(group)
                twins.append({"amount": str(x.amount), "rows": list(group),
                              "why": "same amount, several rows inside the date window"})

    # P3 grouped sums (both directions)
    def grouped(singles, many, single_is_right):
        for s in list(singles):
            if s not in singles:
                continue
            pool = [m for m in many if _within(s, m, days) and m.amount != 0]
            if len(pool) < 2 or len(pool) > group_pool:
                continue
            found = []
            for size in range(2, min(group_max, len(pool)) + 1):
                for combo in itertools.combinations(pool, size):
                    if sum((c.amount for c in combo), Decimal("0")) == s.amount:
                        found.append(combo)
                        if len(found) > 1:
                            break
                if found:
                    break
            if len(found) == 1:
                combo = list(found[0])
                if single_is_right:
                    close("P3", combo, [s], "%d-to-1 batch" % len(combo))
                else:
                    close("P3", [s], combo, "1-to-%d split" % len(combo))
            elif len(found) > 1:
                twins.append({"amount": str(s.amount), "rows": [s.label()],
                              "why": "more than one group of rows adds up to it"})

    grouped(open_r, open_l, True)
    grouped(open_l, open_r, False)

    # P4 tolerance
    if money(tol_abs) > 0 or Decimal(str(tol_pct)) > 0:
        for x in list(open_l):
            if x not in open_l:
                continue
            cands = [y for y in open_r if _within(x, y, days) and (y.amount > 0) == (x.amount > 0)
                     and abs(y.amount - x.amount) <= _tolerance(x.amount, tol_abs, tol_pct)]
            if len(cands) == 1:
                close("P4", [x], cands, "inside tolerance")

    left_only = [x.as_dict() for x in open_l]
    right_only = [y.as_dict() for y in open_r]
    clues = find_clues(open_l, open_r, days)
    lt = sum((x.amount for x in left), Decimal("0"))
    rt = sum((y.amount for y in right), Decimal("0"))
    lo = sum((x.amount for x in open_l), Decimal("0"))
    ro = sum((y.amount for y in open_r), Decimal("0"))
    resid = sum((Decimal(m["residual"]) for m in matches), Decimal("0"))
    bridge = {"left_total": str(lt), "minus_left_only": str(-lo), "plus_right_only": str(ro),
              "plus_residuals": str(resid), "equals": str(lt - lo + ro + resid),
              "right_total": str(rt), "check": str(rt - (lt - lo + ro + resid))}
    return {"matches": matches, "twins": twins, "left_only": left_only,
            "right_only": right_only, "clues": clues, "bridge": bridge,
            "counts": {"left": len(left), "right": len(right), "matched": len(matches),
                       "left_only": len(open_l), "right_only": len(open_r)}}


# ---------------------------------------------------------------- clues

def _digits(a):
    return sorted(str(abs(a)).replace(".", "").lstrip("0"))


def find_clues(open_l, open_r, days=3):
    """Look for known error shapes among leftover rows."""
    clues = []
    for x in open_l:
        for y in open_r:
            a, b = x.amount, y.amount
            if a == b and not _within(x, y, days):
                clues.append({"kind": "LATE", "rows": [x.label(), y.label()],
                              "why": "same amount, %d days apart (outside the window)"
                              % abs((y.day - x.day).days)})
            elif a == b:
                continue  # inside the window: already reported as twins
            elif a == -b and a != 0:
                clues.append({"kind": "SIGN", "rows": [x.label(), y.label()],
                              "why": "same size, opposite sign"})
            elif a != b and _digits(a) == _digits(b) and (a > 0) == (b > 0):
                clues.append({"kind": "SWAP", "rows": [x.label(), y.label()],
                              "why": "same digits in a different order; difference %s is divisible by 9"
                              % (b - a)})
            elif a != 0 and (b == a * 10 or a == b * 10 or b == a * 100 or a == b * 100):
                clues.append({"kind": "SLIDE", "rows": [x.label(), y.label()],
                              "why": "decimal point moved"})
            elif a != 0 and (b == a * 2 or a == b * 2):
                clues.append({"kind": "DOUBLE?", "rows": [x.label(), y.label()],
                              "why": "one is exactly twice the other"})
    for side_rows in (open_l, open_r):
        bucket = {}
        for r in side_rows:
            bucket.setdefault((r.amount, r.day, norm_ref(r.ref)), []).append(r)
        for group in bucket.values():
            if len(group) > 1:
                clues.append({"kind": "REPEAT", "rows": [r.label() for r in group],
                              "why": "same amount, date and ref on one side"})
    return clues


def hint(diff, leftovers=()):
    """Return readable fingerprints for an unexplained difference."""
    d = money(diff)
    out = []
    if d == 0:
        return ["zero: nothing to explain"]
    a = abs(d)
    cents = int((a * 100).to_integral_value())
    if a < 1:
        out.append("under 1.00: rounding, FX conversion or a fee split")
    if cents % 9 == 0:
        out.append("divisible by 9: look for two swapped digits (SWAP) or a moved decimal point (SLIDE)")
    if cents % 2 == 0:
        half = money(a / 2)
        hits = [r for r in leftovers if abs(r.amount) == half]
        msg = "half is %s: an item entered with the wrong sign or on the wrong side would do this" % half
        if hits:
            msg += " (candidates: %s)" % ", ".join(r.label() for r in hits)
        out.append(msg)
    same = [r for r in leftovers if abs(r.amount) == a]
    if same:
        out.append("equals a single leftover row: %s (MISSING on the other side?)"
                   % ", ".join(r.label() for r in same))
    if cents % 10000 == 0:
        out.append("round number: an estimate, an accrual or a typed-in placeholder")
    if not out:
        out.append("no single shape: probably several breaks netting together; "
                   "classify the leftovers one by one instead of chasing the total")
    return out


# ---------------------------------------------------------------- report

def render(result):
    b = result["bridge"]
    lines = ["# Match report", ""]
    c = result["counts"]
    lines.append("Left rows %d, right rows %d, matches %d, left-only %d, right-only %d"
                 % (c["left"], c["right"], c["matched"], c["left_only"], c["right_only"]))
    lines += ["", "## Matches", "", "| pass | left | right | residual | note |", "|---|---|---|---|---|"]
    for m in result["matches"]:
        lines.append("| %s | %s | %s | %s | %s |" % (m["pass"], ",".join(m["left"]),
                     ",".join(m["right"]), m["residual"], m["note"]))
    if result["twins"]:
        lines += ["", "## Twins (not paired, a person decides)", ""]
        for t in result["twins"]:
            lines.append("- %s %s: %s" % (t["amount"], " ".join(t["rows"]), t["why"]))
    for name in ("left_only", "right_only"):
        lines += ["", "## %s" % name.replace("_", "-").capitalize(), ""]
        if not result[name]:
            lines.append("- none")
        for r in result[name]:
            lines.append("- %s %s %s %s %s" % (r["key"], r["date"], r["amount"], r["ref"], r["desc"]))
    lines += ["", "## Clues", ""]
    if not result["clues"]:
        lines.append("- none")
    for k in result["clues"]:
        lines.append("- %s %s: %s" % (k["kind"], " ".join(k["rows"]), k["why"]))
    lines += ["", "## Bridge", "", "| step | amount |", "|---|---|"]
    for key in ("left_total", "minus_left_only", "plus_right_only", "plus_residuals",
                "equals", "right_total", "check"):
        lines.append("| %s | %s |" % (key.replace("_", " "), b[key]))
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- cli

def main(argv=None):
    p = argparse.ArgumentParser(prog="penny.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd")
    pr = sub.add_parser("roll", help="opening + movements == closing?")
    pr.add_argument("csv")
    pr.add_argument("--opening", required=True)
    pr.add_argument("--closing", required=True)
    pm = sub.add_parser("match", help="pair two records")
    pm.add_argument("left")
    pm.add_argument("right")
    pm.add_argument("--days", type=int, default=3)
    pm.add_argument("--tol-abs", default="0")
    pm.add_argument("--tol-pct", default="0")
    pm.add_argument("--group-max", type=int, default=4)
    pm.add_argument("--flip-left", action="store_true")
    pm.add_argument("--flip-right", action="store_true")
    pm.add_argument("--json", action="store_true")
    ph = sub.add_parser("hint", help="fingerprint a difference")
    ph.add_argument("diff")
    ph.add_argument("--leftovers", nargs="*", default=[], help="CSV files of leftover rows")
    a = p.parse_args(argv)
    if a.cmd == "roll":
        rows = load_csv(a.csv, "L")
        computed, gap = roll(a.opening, rows, a.closing)
        print("rows %d  opening %s  movements %s  computed closing %s  stated closing %s  gap %s"
              % (len(rows), money(a.opening), computed - money(a.opening), computed,
                 money(a.closing), gap))
        print("ROLLS" if gap == 0 else "DOES NOT ROLL: fix the population before matching")
        return 0 if gap == 0 else 1
    if a.cmd == "match":
        left = load_csv(a.left, "L", a.flip_left)
        right = load_csv(a.right, "R", a.flip_right)
        res = match(left, right, a.days, a.tol_abs, a.tol_pct, a.group_max)
        print(json.dumps(res, indent=1, ensure_ascii=False) if a.json else render(res))
        return 0
    if a.cmd == "hint":
        rows = []
        for i, f in enumerate(a.leftovers):
            rows += load_csv(f, "LR"[i % 2])
        for line in hint(a.diff, rows):
            print("- " + line)
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
