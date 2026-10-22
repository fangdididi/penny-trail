[English](README.md) | **简体中文**

# Penny Trail（一分钱追踪）

**让两份记录对上，或者精确证明它们为什么对不上。一个给 AI 智能体用的对账技能：把账本和银行之间、订单和结算之间、盘点和系统之间的每一分钱都讲清楚。**

银行说 2,156.63，账上是 2,102.42，差 54.21。这几乎从来不是一个错误：这里一个手误，那里一笔退款记反了方向，一笔没人记的手续费，一张录了两遍的供应商账单，再加一笔还没到账的存款，轧在一起成了个奇怪的数。记一笔"调整 54.21"，这些问题就全部带进下个月。

Penny Trail 是一个用严谨方式做对账的智能体技能：

- **先写配对卡。** 期间、正负号约定、日期窗口、容差和分组规则，在匹配任何一行之前写下来。
- **滚动证明。** 每一边都必须满足 期初 + 发生额 = 期末 才开始匹配。导出不完整在第一分钟就被发现，而不是第三个小时。
- **匹配阶梯。** 由严到宽四轮（参考号、精确金额、分组合计、容差），每一对都记录是哪一轮配上的。
- **双胞胎不猜。** 一行有两个同样好的候选时，智能体停下来问你，而不是悄悄挑一个。
- **六种差异类型。** DRIFT 在途、MISSING 漏记、WRONG 记错、DOUBLE 重复、STRAY 走错门、UNKNOWN 未知，每条都有证据、建议修正、负责人和账龄。
- **差额指纹。** 数字颠倒、小数点错位、正负号反了、重复记账、跨期截止：差额的形状会指向原因。
- **带"未解释"一行的调节表。** 状态为 TIED、TIED-PENDING、OPEN 或 BLOCKED。绝不硬凑。
- **只建议，不录入。** 智能体起草分录和问题，从不动钱，也不改你的账。

## 功能

| | |
|---|---|
| 适用任何一对记录 | 银行 vs 账本、结算 vs 订单、发票 vs 回款、公司卡 vs 报销、盘点 vs 系统、工资 vs 人事、明细账 vs 总账、旧系统 vs 新系统 |
| 完整性证明 | 每边滚动计算、行数核对、常见导出陷阱（筛选、缺页、把小计当成行） |
| 匹配阶梯 | P1 参考号、P2 窗口内精确金额、P3 多对一和一对多精确合计（含手续费的结算）、P4 约定容差且残差可见 |
| 双胞胎处理 | 有歧义的候选从不自动配对 |
| 差异分类 | 六种类型及修正规则和账龄（过期的 DRIFT 升级为 UNKNOWN） |
| 指纹速查 | 算术、时间和结构三类形状，附"能被 9 整除"的原理 |
| 报告 | 配对卡、证明、匹配汇总、差异、双栏调节表、修正清单、结转 |
| 辅助脚本 | `scripts/penny.py`（`roll` / `match` / `hint`），Python 3.8+，仅标准库，金额用 Decimal，只读 |
| 中英双语 | 技能文件、参考资料和完整示例都有中英文版；能识别常见的国内银行流水列名 |

## 安装

技能就是包含 `SKILL.md`（英文）和 `SKILL.zh-CN.md`（中文）的这个文件夹。请整个复制，让 `scripts/`、`references/` 和 `examples/` 一起带上。

**Claude Code**

```bash
git clone https://github.com/fangdididi/penny-trail.git ~/.claude/skills/penny-trail
```

**Codex / 读取 `~/.agents/skills` 的智能体**

```bash
git clone https://github.com/fangdididi/penny-trail.git ~/.agents/skills/penny-trail
```

**Cursor**（项目技能目录）

```bash
git clone https://github.com/fangdididi/penny-trail.git .cursor/skills/penny-trail
```

**其他智能体**（Gemini CLI、Copilot、OpenCode、Windsurf、Cline、Kimi、各类聊天应用）：把 `SKILL.md` 粘贴进它的指令里，或者让它从本仓库地址安装。中文对话请用 `SKILL.zh-CN.md`。没有命令行时用不了辅助脚本，但方法本身可以手工或在表格里照做。

## 使用

把两份导出交给智能体，用大白话提要求：

```
用 penny-trail 把这个月的银行流水和账本对一下，差额每一分钱都要说清楚。
平台结算打款 8,412.07，可我的订单是 8,950.00，帮我查差额去哪了。
盘点表和库存系统有 40 个 SKU 对不上，帮我逐一核对。
Here's my September bank CSV and my cash book export. Reconcile them with penny-trail.
```

智能体会：

1. 写配对卡，并和你确认日期窗口、容差和正负号约定。
2. 证明每一边能从期初滚到期末（否则以 BLOCKED 停下，并说明缺了什么）。
3. 统一两个文件的格式，运行匹配阶梯。
4. 把双胞胎拿给你看，问你单据支持哪种配对。
5. 给每条剩余行归类，查指纹，并逐条用原始单据确认。
6. 生成调节表，给出状态、修正清单和结转清单。

辅助命令：

```bash
python3 scripts/penny.py roll bank.csv --opening 4200.00 --closing 2156.63   # 这一边滚得平吗？
python3 scripts/penny.py match books.csv bank.csv --days 3 --group-max 4     # 阶梯 + 线索 + 调节核对
python3 scripts/penny.py match books.csv bank.csv --json                     # 机器可读输出
python3 scripts/penny.py hint 54.21                                          # 这个差额是什么形状？
python3 -m unittest discover -s tests -v                                     # 自检
```

CSV 需要 `date` 和 `amount` 两列；`id`、`ref`、`desc`、`party` 可选。常见别名（`posting date`、`memo`、`payee`、`交易日期`、`交易金额`、`摘要` 等）都能识别。某一边把收入记为负数时，用 `--flip-left` / `--flip-right` 整边取反。收入、支出分两列的流水，请先合并成一个带符号金额。

## 示例

`examples/lantern-tea/` 是一家虚构茶叶铺 9 月的现金账和银行对账单。

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

完整报告 `examples/lantern-tea/REPORT.zh-CN.md` 把 54.21 的差额拆成七件独立的事（一笔 DOUBLE、两笔 WRONG、两笔 MISSING、两笔 DRIFT），调节表以 0.00 收尾，给出五笔建议分录，并为两笔在途项定下复查日期。

## 文件结构

```
penny-trail/
├── SKILL.md                     # 技能（英文）
├── SKILL.zh-CN.md               # 技能（中文）
├── README.md
├── README.zh-CN.md
├── LICENSE
├── scripts/
│   └── penny.py                 # roll / match / hint
├── references/
│   ├── fingerprints.md          # 差额形状及确认方法（英文）
│   └── fingerprints.zh-CN.md    # 中文版
├── examples/
│   └── lantern-tea/             # books.csv、bank.csv、REPORT.md、REPORT.zh-CN.md
└── tests/
    └── test_penny.py
```

## 基本原则

- 先定规则再看数据；之后的任何改动都记在配对卡上。
- 两边都滚平之前不做匹配。
- 用精确小数，绝不用浮点数。
- 双胞胎由人决定，并写下理由。
- 解释不了的金额保持可见，绝不硬凑。
- 差异按总额逐笔修正，不按净额。
- 智能体只提出分录，由人录入。Penny Trail 不构成会计或税务建议。
- 对账单留在你自己的机器上；报告中账号打码。

## 许可证

[MIT](LICENSE)
