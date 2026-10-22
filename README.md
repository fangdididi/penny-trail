**English** | [简体中文](README.zh-CN.md)

# Penny Trail

**Make two records agree, or prove exactly why they don't. A reconciliation skill for AI agents that explains every cent between your books and the bank, your orders and the payout, your count and the system.**

The bank says 2,156.63. Your books say 2,102.42. The gap is 54.21, and it is almost never one mistake. It is a typo here, a refund booked the wrong way there, a fee nobody recorded, a supplier bill entered twice, and a deposit that hasn't landed yet, all netting to an odd number. Post one "adjustment 54.21" and every one of them survives into next month.

Penny Trail is an agent skill that does reconciliation the careful way:

- **Pair card first.** Period, sign convention, date window, tolerance and grouping are written down before any row is matched.
- **Roll-forward proof.** Each side must satisfy opening + movements = closing before matching starts. Incomplete exports are caught in minute one, not hour three.
- **Match ladder.** Four passes from strict to loose (reference, exact amount, grouped sums, tolerance). Every pairing records which pass made it.
- **No guessing between twins.** When one row has two equally good partners, the agent stops and asks instead of silently picking one.
- **Six break types.** DRIFT, MISSING, WRONG, DOUBLE, STRAY, UNKNOWN, each with evidence, a proposed fix, an owner and an age.
- **Fingerprints.** Swapped digits, moved decimal points, wrong signs, duplicates, cut-off slips: the shape of a difference points at its cause.
- **Bridge with an unexplained line.** Status TIED, TIED-PENDING, OPEN or BLOCKED. No plugs, ever.
- **Propose, never post.** The agent drafts entries and questions. It never moves money or edits your ledger.

## Features

| | |
|---|---|
| Works on any pair | bank vs books, payouts vs orders, invoices vs payments, card feed vs expenses, stock count vs system, payroll vs HR, sub-ledger vs GL, old system vs new |
| Population proof | roll-forward per side, row counts, typical export traps (filters, missing pages, subtotals read as rows) |
| Match ladder | P1 reference, P2 exact amount in window, P3 N-to-1 and 1-to-N exact sums (payouts with fees), P4 stated tolerance with visible residuals |
| Twin handling | ambiguous candidates are never auto-paired |
| Break taxonomy | six types with fix rules and ageing (stale DRIFT becomes UNKNOWN) |
| Fingerprint guide | arithmetic, timing and structural shapes, with the divisible-by-9 reasoning |
| Report | pair card, proof, match summary, breaks, two-column bridge, fix list, carry-forward |
| Helper script | `scripts/penny.py` (`roll` / `match` / `hint`), Python 3.8+, standard library only, Decimal money, read-only |
| Bilingual | full English and Chinese skill files, references and worked example; understands common Chinese bank column names |

## Installation

The skill is the folder containing `SKILL.md` (English) and `SKILL.zh-CN.md` (Chinese). Copy the whole folder so `scripts/`, `references/` and `examples/` come with it.

**Claude Code**

```bash
git clone https://github.com/fangdididi/penny-trail.git ~/.claude/skills/penny-trail
```

**Codex / agents that read `~/.agents/skills`**

```bash
git clone https://github.com/fangdididi/penny-trail.git ~/.agents/skills/penny-trail
```

**Cursor** (project skills folder)

```bash
git clone https://github.com/fangdididi/penny-trail.git .cursor/skills/penny-trail
```

**Any other agent** (Gemini CLI, Copilot, OpenCode, Windsurf, Cline, Kimi, chat apps): paste `SKILL.md` into its instructions, or ask it to install the skill from this repository URL. For Chinese conversations, use `SKILL.zh-CN.md`. Without a shell you lose the helper script, but the method works by hand or in a spreadsheet.

## Usage

Hand the agent two exports and ask in plain words:

```
Here's my September bank CSV and my cash book export. Reconcile them with penny-trail.
The payout was 8,412.07 but my orders say 8,950.00. Find out where the difference went.
Our stock count and the inventory system disagree on 40 SKUs. Tie them out.
用 penny-trail 把这个月的银行流水和账本对一下，差额每一分钱都要说清楚。
```

The agent will:

1. Write the pair card and confirm the window, tolerance and sign convention with you.
2. Prove each side rolls from opening to closing (or stop with BLOCKED and say what is missing).
3. Normalise both files and run the match ladder.
4. Show you any twins and ask which pairing the documents support.
5. Classify every leftover, check fingerprints, and confirm each against a source document.
6. Build the bridge and give a status, the fix list and the carry-forward list.

Helper commands:

```bash
python3 scripts/penny.py roll bank.csv --opening 4200.00 --closing 2156.63   # does this side roll?
python3 scripts/penny.py match books.csv bank.csv --days 3 --group-max 4     # ladder + clues + bridge check
python3 scripts/penny.py match books.csv bank.csv --json                     # machine-readable
python3 scripts/penny.py hint 54.21                                          # what shape is this gap?
python3 -m unittest discover -s tests -v                                     # self-test
```

CSV files need a `date` and an `amount` column; `id`, `ref`, `desc` and `party` are optional. Common aliases (`posting date`, `memo`, `payee`, `交易日期`, `交易金额`, `摘要` ...) are recognised. Use `--flip-left` / `--flip-right` when one side records money in as negative.

## Example

`examples/lantern-tea/` holds a fictional tea shop's September cash book and bank statement.

```
$ python3 scripts/penny.py match examples/lantern-tea/books.csv examples/lantern-tea/bank.csv
| pass | left | right | residual | note |
| P1 | L01 | R01 | 0.00 | same ref |
| P2 | L07 | R04 | 0.00 | +0 days |
| P2 | L10 | R06 | 0.00 | +1 days |
| P3 | L02,L03,L04,L05 | R02 | 0.00 | 4-to-1 batch |

## Twins (not paired, a person decides)
- -226.80 L:L08 L:L09 R:R05: same amount, several rows inside the date window

## Clues
- SWAP L:L06 R:R03: same digits in a different order; difference 360.00 is divisible by 9
- SIGN L:L13 R:R07: same size, opposite sign
- REPEAT L:L08 L:L09: same amount, date and ref on one side
```

The full report in `examples/lantern-tea/REPORT.md` turns the 54.21 gap into seven separate items (one DOUBLE, two WRONG, two MISSING, two DRIFT), a bridge that ends in 0.00, five proposed entries and a recheck date for the two items still in flight.

## File structure

```
penny-trail/
├── SKILL.md                     # the skill (English)
├── SKILL.zh-CN.md               # the skill (Chinese)
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   └── penny.py                 # roll / match / hint
├── references/
│   ├── fingerprints.md          # shapes of a difference and how to confirm them
│   └── fingerprints.zh-CN.md
├── examples/
│   └── lantern-tea/             # books.csv, bank.csv, REPORT.md, REPORT.zh-CN.md
└── tests/
    └── test_penny.py
```

## Ground rules

- Rules before rows; any later change is noted on the pair card.
- No matching until both sides roll.
- Exact decimals, never floats.
- Twins are decided by a person, with a written reason.
- Unexplained amounts stay visible. No plugs.
- Fix breaks gross, not net.
- The agent proposes entries; a person posts them. Penny Trail is not accounting or tax advice.
- Statements stay on your machine; account numbers are masked in reports.

## License

[MIT](LICENSE)
