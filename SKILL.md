---
name: penny-trail
description: Reconcile any two records that should agree (bank statement vs books, payment-provider payouts vs orders, invoices vs payments, platform report vs spreadsheet, stock count vs system, payroll file vs HR list) and explain every cent of the gap. Freezes the rules before matching, proves each side is complete with a roll-forward, pairs rows in strict-to-loose passes without guessing between look-alikes, sorts what is left into six break types, reads the shape of each difference (swapped digits, wrong sign, moved decimal, double entry, cut-off), and closes with a bridge where the unexplained line is zero or the recon stays open. Proposes fixes for a person to post; never moves money or edits a ledger. Use when two numbers that should match do not, at month-end, before filing, after a messy export, or when someone asks "why is the bank different from my books".
---

# Penny Trail

> Two records disagree by 54.21. That is not one problem. It is usually five small ones that happen to net to an odd number.

## What this skill is

Penny Trail is a method for making two records agree, or proving exactly why they do not. It works on any pair of lists that describe the same money or the same things from two points of view:

| Inside view ("what we wrote down") | Outside view ("what actually happened") |
|---|---|
| bookkeeping cash account | bank or card statement |
| order export from the shop | payment-provider payout report |
| invoice register | customer payments received |
| expense spreadsheet | corporate card feed |
| stock system | physical count sheet |
| payroll run | HR headcount and contracts |
| sub-ledger (AR, AP, fixed assets) | general ledger control account |

You come out with:

1. A **pair card** that fixes the period, sign convention, date window and tolerance *before* any matching.
2. A **roll-forward proof** for each side: opening + movements = closing. If a side does not roll, you stop.
3. A **match table** where every pairing records which pass made it (P1-P4), and look-alike rows are left for a person instead of being guessed.
4. A **break list**: every leftover row with one of six types (DRIFT, MISSING, WRONG, DOUBLE, STRAY, UNKNOWN), evidence, a proposed fix, an owner and an age.
5. A **bridge** that walks one side's balance to the other's, line by line, ending in an *unexplained* line.
6. A **status**: TIED, TIED-PENDING, OPEN or BLOCKED, plus a carry-forward list that the next run must check.

## The problem it solves

- **Matching before proving.** People start pairing rows from an export that is missing a page, a filter, or the last two days. Hours later the gap is still there, because it was never in the rows.
- **Netting hides errors.** A +360 typo and a -306 missing deposit look like a 54 problem. Fixing "the 54" with one entry buries two real mistakes.
- **Greedy matching.** Two 226.80 payments in the books and one at the bank: a tool picks one and silently treats the other as fine. The duplicate survives.
- **Plugs.** "Miscellaneous adjustment 54.21" makes the numbers tie and makes next month harder.
- **Timing items that never clear.** "Deposit in transit" is still in transit four months later. Nobody checks.
- **Floats and formats.** 0.1 + 0.2, `(80.00)` for negatives, debit columns vs signed amounts, day/month swaps, timezones at midnight. Each creates fake breaks.

## When to use it

- A bank, card, wallet or payment-provider balance differs from the books.
- Month-end, quarter-end, year-end close, or before a tax filing or audit.
- A payout lumps many sales, fees and refunds into one deposit and you need to tie it back.
- Two systems were migrated, merged or synced and you need proof nothing was lost.
- A count (stock, seats, licenses, headcount) differs from the system of record.
- Someone says "it's only a few dollars off": small gaps often hide large offsetting errors.

Not for: forecasting, budgeting, explaining *why* the business changed (that is variance analysis), or tax advice. Penny Trail explains differences between records; a qualified person signs off.

## Ground rules

1. **Rules before rows.** Window, tolerance and sign convention are written down before the first match. Changing them later is allowed only with a note in the pair card saying what changed and why.
2. **Prove the population first.** No matching until each side rolls from opening to closing.
3. **Decimals, not floats.** Every amount is parsed as an exact decimal and rounded once, to the currency's minor unit.
4. **No guessing between look-alikes.** If one row has two equally good partners, nobody is paired automatically. A person decides, and the decision is written down.
5. **No plugs.** An unexplained amount stays visible as UNKNOWN. It is never absorbed into a "misc" entry to make the bridge balance.
6. **Gross, not net.** Fix each break separately even when two of them cancel out.
7. **Propose, never post.** The skill drafts adjusting entries and messages. It does not post to a ledger, move money, contact a bank, or change source data.
8. **Read only what the user handed over.** Statements and ledgers are private. Do not upload them anywhere, and mask account numbers in the report (keep the last four digits).

## Step by step

### Step 0. Pair card

Write a short card at the top of the work file before opening the data:

```text
PAIR CARD
inside view:   Lantern Tea cash book (books.csv), exported 2026-10-01
outside view:  Harbour Bank current account ****4471 (bank.csv), statement 2026-09
period:        2026-09-01 .. 2026-09-30, inclusive, local date (Europe/London)
authority:     bank wins on what cleared and when; books win on what it was for
sign:          + money in, - money out on both sides (bank debit column flipped)
currency:      GBP only; anything else is STRAY until explained
date window:   3 calendar days (card payouts settle T+2, weekends)
tolerance:     0.00 (no fees expected inside single payments)
grouping:      payouts may bundle up to 4 book rows (sales minus fees)
target:        unexplained = 0.00; every DRIFT item dated
```

Choose tolerance from what can genuinely differ: a fixed transfer fee, FX rounding, a per-payout charge. If you cannot name the cause, tolerance is zero.

### Step 1. Prove each side

For each side separately:

```text
opening balance + sum of movements = closing balance
```

- Take opening and closing from the document itself (statement header, trial balance), not from your own sum.
- If it does not roll, the export is incomplete or filtered: missing pages, a status filter (only "posted"), a date filter in the wrong timezone, hidden rows, header/footer totals read as movements. Status **BLOCKED**. Fix the export, then start again.
- Also compare row counts with the source if it shows them.

Helper: `python3 scripts/penny.py roll bank.csv --opening 4200.00 --closing 2156.63`

### Step 2. Same language

Normalise both sides into one shape: `id, date, amount, ref, desc, party`.

- **Sign.** Pick one convention. Convert debit/credit columns into one signed amount. Flip a whole side if needed (`--flip-right`), never row by row.
- **Dates.** One timezone, date only. Watch day/month order (03/09 can be 3 Sep or 9 Mar: check a row where the day is above 12).
- **References.** Keep the raw text and also a cleaned key: lower case, digits and letters only (`HL-2291` and `hl2291` become the same key).
- **Amounts.** Strip currency marks and thousands separators; `(80.00)` and `80.00-` mean negative.
- **Out of scope rows.** Opening-balance lines, running-balance columns, subtotals and page totals are not movements. Remove them and say so.

### Step 3. Match ladder

Run passes from strict to loose. A row leaves the pool the moment it is paired. Record the pass on every match.

| Pass | Rule | Typical catch |
|---|---|---|
| P1 | same cleaned reference and same amount | invoices, cheques, standing orders |
| P2 | same amount, dates inside the window, exactly one candidate each way | most card and transfer lines |
| P3 | one row equals the exact sum of 2..N rows on the other side, inside the window | payouts (sales - fees - refunds), split payments, batch deposits |
| P4 | amounts within the stated tolerance, one candidate | FX rounding, fixed bank charges deducted from a transfer |

**Twins.** When a row has more than one equally good partner (two 226.80 book rows, one 226.80 bank row), stop and list them as twins. Look at references, descriptions and source documents. Pair the one you can justify; the other becomes a leftover. Write the reason.

P4 matches carry a *residual* (the small difference). Residuals are not hidden: they appear in the bridge and usually need their own entry (bank charge, FX gain or loss).

Helper: `python3 scripts/penny.py match books.csv bank.csv --days 3 --group-max 4`

### Step 4. Sort the leftovers

Every row nobody claimed gets exactly one type:

| Type | Meaning | Usual fix |
|---|---|---|
| **DRIFT** | real and correct, just not on the other side yet (deposit in transit, uncleared cheque, payout in flight, goods received not invoiced) | none now; give an expected clear date and check next run |
| **MISSING** | happened, but one side never recorded it (bank fee, interest, direct debit, forgotten sale) | add the entry on the side that lacks it |
| **WRONG** | both sides have it but disagree (amount, sign, date across period end, account, currency) | correct the wrong side; the other side is the evidence |
| **DOUBLE** | recorded twice on one side (re-import, manual + bank feed, retried webhook) | reverse the extra one |
| **STRAY** | does not belong in this pair (another account, entity, currency, or period) | move it where it belongs; remove from this recon |
| **UNKNOWN** | no explanation yet | stays open with an owner; never plugged |

Rules of thumb:

- DRIFT must be dated. A DRIFT older than its normal cycle (say 10 business days for a cheque, 5 for a deposit) becomes UNKNOWN and is investigated.
- WRONG and DOUBLE are usually on the inside view: bank lines rarely duplicate; bookkeeping imports often do.
- A STRAY in this recon is often a MISSING in another one. Tell the user which.

### Step 5. Read the fingerprints

Leftovers and the total gap often have a recognisable shape. Check these before searching by hand:

| Shape | Clue | Likely cause |
|---|---|---|
| SWAP | same digits, different order (1,845 vs 1,485); difference divisible by 9 | transposed digits when typing |
| SLIDE | one amount is 10x or 100x the other; difference divisible by 9 | decimal point moved (45.00 vs 450.00) |
| SIGN | same size, opposite sign; total gap = 2x the item | refund booked as income, debit taken as credit |
| DOUBLE? | one amount is twice the other, or two identical rows on one side | entered twice, or a half-payment |
| LATE | same amount, dates beyond the window, often across period end | cut-off, weekend, holiday, wrong year typed |
| EXACT | total gap equals one leftover row | that row is MISSING on the other side |
| ROUND | gap is a round number (100.00, 500.00) | estimate, accrual, petty cash, placeholder |
| CENTS | gap under 1.00 | rounding, FX, fee split, tax rounding per line vs per invoice |

Helper: `python3 scripts/penny.py hint 54.21` and the *Clues* section of the match report. More shapes and checks are in `references/fingerprints.md`.

A fingerprint is a lead, not a verdict. Confirm each one against a source document (receipt, invoice, bank detail, order page) before classifying.

### Step 6. Bridge and status

Walk from one side's closing balance to the other's. Use the standard two-column form when one side is a bank:

```text
Balance per bank statement                 2,156.63
  + deposits in transit (DRIFT)              520.00
  - uncleared cheques (DRIFT)                (95.00)
Adjusted bank balance                      2,581.63

Balance per books                          2,102.42
  + reverse duplicate PK-118 (DOUBLE)        226.80
  + correct HL-2291 1,845 -> 1,485 (WRONG)   360.00
  - fix sign of refund 7731 (WRONG)          (96.00)
  - bank fee not recorded (MISSING)          (12.00)
  + interest not recorded (MISSING)            0.41
Adjusted book balance                      2,581.63

Unexplained                                    0.00
```

Status:

| Status | Condition |
|---|---|
| **TIED** | unexplained is 0 (or within the materiality limit written on the pair card) and no DRIFT items |
| **TIED-PENDING** | unexplained is 0, but DRIFT items remain; each has an expected clear date and a recheck date |
| **OPEN** | anything UNKNOWN remains, or a twin is undecided, or unexplained is not 0 |
| **BLOCKED** | a side did not roll in Step 1; no matching was done |

### Step 7. Fix list and carry-forward

Produce, for the user to act on:

1. **Proposed entries**, one per break, never netted: date, account or category, amount, description, the break id it clears, the evidence.
2. **Questions to ask** someone else (supplier, payment provider, bank, colleague), each with the exact row and amount.
3. **Carry-forward list**: every DRIFT and UNKNOWN with first-seen date, expected clear date and owner. The next run starts by checking this list: anything that should have cleared and did not is promoted to UNKNOWN.
4. **Process note** when the same break type keeps returning (duplicate imports every month, fees never booked): suggest the upstream fix, such as a bank rule, an import dedupe key, or a recurring entry.

## Report layout

```text
# Recon: <inside> vs <outside>, <period>   Status: TIED-PENDING
Pair card            (Step 0, including any rule changes)
Population proof     (both roll-forwards with figures)
Match summary        (counts per pass, twins and how each was decided)
Breaks               (id, type, rows, amount, evidence, proposed fix, owner, age)
Bridge               (two columns, unexplained line)
Fix list             (entries, questions)
Carry-forward        (DRIFT and UNKNOWN with dates)
```

A complete worked example is in `examples/lantern-tea/REPORT.md`.

## Examples

**Small shop, bank vs cash book.** Books show 2,102.42, bank shows 2,156.63, gap 54.21. Both sides roll. The ladder pairs rent by reference (P1), a cash deposit and an electricity bill by amount (P2), and a card payout of 1,046.35 against three days of sales minus fees (P3). Two identical 226.80 packaging rows meet one bank line: twins. The person checks the supplier statement, pairs one, and the other is DOUBLE. Clues flag 1,845 vs 1,485 (SWAP) and +48 vs -48 (SIGN). Bank fee and interest are MISSING. A month-end cash deposit and an uncleared cheque are DRIFT. Unexplained: 0.00, status TIED-PENDING with a recheck on 6 October.

**Payment provider payout.** "The payment provider paid 8,412.07 but my orders say 8,950.00." Treat the payout report as the outside view, the order export as the inside view, first split both files by payout id (the provider reports one), then run the ladder inside each payout so grouping stays small. Breaks: refunds and a chargeback (MISSING in the order total), fees (MISSING), one order paid in another currency (STRAY to the FX recon).

**Stock count.** Inside: system quantities; outside: count sheet. Amount = units. A SLIDE (12 vs 120) points at a unit-of-measure mix-up (box vs piece); a cluster of LATE rows points at goods received after the count cut-off.

**Two-system migration.** Old CRM invoices vs new billing system after an import. Both sides must roll to the same total. DOUBLE dominates (retried batches); STRAY catches test records.

## Tips

- If the gap is large and round, look for a whole missing day or page before touching individual rows.
- Sort leftovers by amount, not date. Twins, swaps and doubles sit next to each other.
- Do card payouts per payout id first; open grouping across a whole month explodes and invents coincidences.
- Raise the date window only with a reason (holiday, settlement cycle) and write it on the pair card.
- A tie with many P4 matches deserves a second look: tolerance can quietly hide real differences.
- Keep the source files untouched; work on copies and note their export time.
- For Chinese bank statements, columns like 交易日期 / 交易金额 / 摘要 / 对方户名 are understood by the helper; 收入/支出 split columns must be merged into one signed amount first.

## Helper script

`scripts/penny.py` (Python 3.8+, standard library only, read-only):

| Command | What it does |
|---|---|
| `roll FILE --opening X --closing Y` | proves one side rolls; exit code 1 if not |
| `match LEFT RIGHT [--days N] [--tol-abs A] [--tol-pct P] [--group-max K] [--flip-left/--flip-right] [--json]` | runs P1-P4, lists twins, leftovers, clues and a bridge check |
| `hint DIFF [--leftovers L.csv R.csv]` | reads the shape of a difference |

The script never decides a twin, never classifies a break by itself and never writes to the input files. Run the tests with `python3 -m unittest discover -s tests`.
