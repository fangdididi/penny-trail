# Recon: Lantern Tea cash book vs Harbour Bank ****4471, September 2026

**Status: TIED-PENDING** (unexplained 0.00; two DRIFT items to recheck on 2026-10-06)

Lantern Tea is a fictional one-shop tea seller. Files: `books.csv` (inside view), `bank.csv` (outside view). Commands used are shown so you can rerun them.

## Pair card

```text
inside view:   cash book export, 2026-10-01 09:12
outside view:  Harbour Bank statement ****4471, September 2026
period:        2026-09-01 .. 2026-09-30 inclusive, Europe/London dates
authority:     bank wins on what cleared and when; books win on what it was for
sign:          + in, - out on both sides
currency:      GBP
date window:   3 calendar days
tolerance:     0.00
grouping:      up to 4 book rows per bank row (card payouts)
target:        unexplained 0.00, every DRIFT item dated
rule changes:  none
```

## Population proof

| Side | Opening | Movements | Computed closing | Stated closing | Gap |
|---|---:|---:|---:|---:|---:|
| Bank | 4,200.00 | -2,043.37 | 2,156.63 | 2,156.63 (statement footer) | 0.00 |
| Books | 4,200.00 | -2,097.58 | 2,102.42 | 2,102.42 (trial balance) | 0.00 |

```bash
python3 scripts/penny.py roll examples/lantern-tea/bank.csv  --opening 4200.00 --closing 2156.63   # ROLLS
python3 scripts/penny.py roll examples/lantern-tea/books.csv --opening 4200.00 --closing 2102.42   # ROLLS
```

Both roll. Gap to explain: 2,156.63 - 2,102.42 = **54.21**.

## Match summary

```bash
python3 scripts/penny.py match examples/lantern-tea/books.csv examples/lantern-tea/bank.csv --days 3 --group-max 4
```

| Pass | Books | Bank | Note |
|---|---|---|---|
| P1 | L01 rent -1,800.00 | R01 | same reference RENT-09 |
| P2 | L07 cash deposit 640.00 | R04 | same day |
| P2 | L10 electricity -158.33 | R06 | +1 day |
| P3 | L02 + L03 + L04 + L05 (412.00 + 389.50 + 275.00 - 30.15) | R02 payout 1,046.35 | 4-to-1 batch |

**Twins:** L08 and L09 (both -226.80, PK-118) against R05 (-226.80). The supplier statement lists PK-118 once and the bank paid once. Decision: pair L08 with R05 (by hand, reason recorded); L09 goes to the breaks.

## Breaks

| Id | Type | Rows | Amount effect on books | Evidence | Proposed fix | Owner | Age |
|---|---|---|---:|---|---|---|---|
| B1 | DOUBLE | L09 | +226.80 | supplier statement shows PK-118 once; REPEAT clue | reverse L09 | owner | 7 days |
| B2 | WRONG | L06 vs R03 | +360.00 | invoice HL-2291 total is 1,485.00; SWAP clue (1,845 vs 1,485) | correct L06 to -1,485.00 | owner | 22 days |
| B3 | WRONG | L13 vs R07 | -96.00 | refund left the account; SIGN clue | change L13 from +48.00 to -48.00 | owner | 12 days |
| B4 | MISSING | R08 | -12.00 | monthly account fee on statement | add bank charges -12.00 dated 30 Sep | owner | 0 days |
| B5 | MISSING | R09 | +0.41 | credit interest on statement | add interest income +0.41 dated 30 Sep | owner | 0 days |
| B6 | DRIFT | L11 | (bank side) +520.00 | deposit slip dated 30 Sep, after branch cut-off | none; expect on statement by 2 Oct | owner | 0 days |
| B7 | DRIFT | L12 | (bank side) -95.00 | cheque 1043 handed over 28 Sep | none; expect clearing by 6 Oct | owner | 2 days |

## Bridge

```text
Balance per bank statement                 2,156.63
  + deposit in transit (B6)                  520.00
  - uncleared cheque 1043 (B7)               (95.00)
Adjusted bank balance                      2,581.63

Balance per books                          2,102.42
  + reverse duplicate PK-118 (B1)            226.80
  + correct HL-2291 (B2)                     360.00
  - fix sign of refund 7731 (B3)             (96.00)
  - bank fee (B4)                            (12.00)
  + interest (B5)                              0.41
Adjusted book balance                      2,581.63

Unexplained                                    0.00
```

Note that the five book fixes net to +479.21 and the two DRIFT items to +425.00. Their difference is the 54.21 gap. A single "adjustment 54.21" would have hidden all seven.

## Fix list (for the owner to post)

1. Reverse L09 (duplicate PK-118), +226.80 to cash, -226.80 to packaging.
2. Correct L06 from -1,845.00 to -1,485.00 (invoice HL-2291).
3. Correct L13 refund 7731 from +48.00 to -48.00.
4. New entry 2026-09-30: bank charges -12.00.
5. New entry 2026-09-30: interest income +0.41.

Questions: none outside the business.

Process note: the duplicate came from importing the supplier bill and also typing it. Suggest one entry path for supplier bills.

## Carry-forward

| Item | First seen | Expected clear | Recheck | If not cleared |
|---|---|---|---|---|
| B6 deposit 520.00 | 2026-09-30 | 2026-10-02 | 2026-10-06 | promote to UNKNOWN, ask the bank branch |
| B7 cheque 1043 -95.00 | 2026-09-28 | 2026-10-06 | 2026-10-06 | ask Mo's Repairs whether it was received |
