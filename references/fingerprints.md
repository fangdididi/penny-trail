# Fingerprints of a difference

A quick field guide for Step 5. Each shape is a lead; confirm with a source document before you classify a break.

## Arithmetic shapes

| Shape | How to test | What usually happened | Confirm with |
|---|---|---|---|
| SWAP | both amounts use the same digits; difference / 9 is a whole number of cents | two digits typed in the wrong order (1,845 -> 1,485) | invoice or receipt |
| SLIDE | one amount is 10x, 100x or 1000x the other; difference / 9 is whole | decimal point moved, or cents typed as units (4500 -> 45.00) | receipt, unit price x quantity |
| SIGN | same size, opposite sign; the total gap is twice the item | refund booked as income, credit note booked as invoice, debit/credit columns read the wrong way | the payment direction on the statement |
| HALF | gap is even and half the gap equals a leftover | same as SIGN, seen from the total | the leftover row |
| EXACT | gap equals one leftover row | that row is MISSING on the other side | the source of that row |
| PAIR SUM | gap equals the sum of two leftovers | two MISSING rows, or a MISSING plus a DOUBLE | both sources |
| ROUND | gap is 10, 50, 100, 500 ... | estimate, accrual, petty cash top-up, placeholder typed during close | who keyed it |
| CENTS | gap under 1.00 | per-line vs per-invoice tax rounding, FX conversion, fee split | the calculation |
| REPEAT | identical amount, date and reference twice on one side | re-import, manual entry plus bank feed, retried webhook | import log |

## Timing shapes

| Shape | Signal | Typical cause |
|---|---|---|
| LATE | same amount on both sides, dates outside the window | weekend or holiday settlement, wrong year typed, period cut-off |
| EDGE | leftovers cluster on the first or last two days of the period | cut-off: recorded in one period on one side, the next on the other |
| MIDNIGHT | rows near 00:00 move by one day | timezone used for export differs between the two systems |
| STALE | a DRIFT item older than its normal cycle | lost cheque, rejected deposit, payout held for review |

## Structural shapes

| Shape | Signal | Typical cause |
|---|---|---|
| WHOLE DAY | gap equals one day's movements on one side | export filter, missing statement page |
| ONE PARTY | all leftovers share a counterparty | supplier paid from another account, or account mapping error (STRAY) |
| ONE CURRENCY | leftovers are all in a second currency | multi-currency rows mixed into a single-currency recon (STRAY) |
| ONE SIZE | many leftovers of the same small amount | a recurring fee never booked (MISSING); suggest a recurring entry |
| BATCH | one large outside row, many small inside rows nearby | payout or batch deposit; run P3 per batch id |

## Divisible-by-9: why it works

Swapping two digits that sit in positions i and j changes the value by (a - b) x (10^i - 10^j), and every 10^i - 10^j is a multiple of 9. Moving a decimal point multiplies the value by 10^k, and 10^k - 1 is also a multiple of 9. So both errors leave a difference divisible by 9. The converse is not true: many differences divisible by 9 have nothing to do with typing. Use it to choose where to look, not to conclude.

## Before calling something UNKNOWN

1. Is the population proof still valid (did someone re-export)?
2. Did you check the twins list?
3. Did you try the gap against single leftovers, pairs of leftovers, and twice each leftover?
4. Did you look one period back and one forward for the same amount?
5. Did you check other accounts of the same owner for a STRAY?

If all five are done and nothing fits, UNKNOWN is the honest answer. Give it an owner and a date.
