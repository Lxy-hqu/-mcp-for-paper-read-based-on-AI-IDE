# 使用说明

[项目首页](../README.zh-CN.md) · [示例](example.md) · [验证范围](validation.md) · [MCP 兼容说明](mcp-guide.md)

## 安装技能

先在本机安装 Python 3.10+ 与 Git，再执行：

```bash
git clone https://github.com/Lxy-hqu/-mcp-for-paper-read-based-on-AI-IDE.git paper-research-mentor
cd paper-research-mentor
python tools/install_skill.py
```

在 Windows PowerShell 中，若使用 Python Launcher，可以将 `python` 换成 `py -3`；先确认其对应版本不低于 3.10。不同系统都使用同一个安装脚本。

默认目标为 `$CODEX_HOME/skills/paper-research-mentor`；未设置 `CODEX_HOME` 时为用户主目录的 `.codex/skills/paper-research-mentor`。需要指定另一套 Codex 用户目录时：

```bash
python tools/install_skill.py --codex-home /path/to/your/codex-home
```

安装器复制18个可复用源文件，比较安装副本与源码哈希；不同的已有版本先保存到用户目录下的 `skill-backups/`，备份不进入技能发现目录。ZIP 和本机清单生成于 `dist/`，不提交到仓库。

也可以手工把整个 `paper-research-mentor/` 文件夹复制到用户技能目录，确保其中包含 `SKILL.md`。不要仅复制入口文档而漏掉脚本和参考规则。

如果当前聊天未显示新技能，重新打开聊天或重启 Codex。技能允许自动匹配相关阅读请求；明确使用 `$paper-research-mentor` 可以指定它。不同宿主的工具和权限配置会影响具体可执行能力。

## 依赖检查

```bash
python paper-research-mentor/scripts/mentor.py doctor
```

| 功能 | 所需能力 |
|---|---|
| 文本导入、记录、SQLite、检查和导出 | Python 标准库 |
| PDF 文本与坐标 | Poppler 的 `pdftotext`，`pdfinfo` 辅助；pypdf 可作文本后备 |
| PDF 页面渲染 | Poppler 的 `pdftoppm` 或 PyMuPDF |
| 扫描页 OCR | Tesseract、对应语言包和页面渲染器 |
| 算术表达式 AST | Python 标准库，受限语法，不执行输入 |
| 可选符号结构 | SymPy；不等于自动验证证明 |
| 可选本地模型辅助 | 已部署的 Ollama，需要明确指定模型 |

安装 pypdf 等 Python 库不会自动安装 Poppler 或 Tesseract。缺少能力时会明确报告限制；需要图像核对的内容不能因文本提取成功就算完全验证。技能没有强制依赖原 MCP 或 Node.js。

## 输入与产物

支持本地 PDF、UTF-8 文本/Markdown、论文链接和多篇材料。论文正文、附录、官方代码、外部知识与用户项目材料分别登记；链接指向摘要页时，Codex 需先定位实际全文，不能将网页摘要当成整篇阅读。

默认用户库位于当前工作区的 `paper-reading/`。可在请求中指定其他目录。原始输入保留，处理副本、逐页文本与渲染图放到用户库；结构化记录存于 SQLite。资料不会进入已安装技能目录。

一次运行通常包括：

- 总览及问题—假设—方法—证据—结论的完整解释。
- 核心公式、符号表、推导、图表分析与条件边界。
- 适用的伪代码、配置和复现材料，并明确实际验证层级。
- 有来源及适用条件的术语、搭配、句式和段落结构。
- 项目方法建议或条件化迁移方向；多篇输入增加综合比较。
- 讨论问题卡、参考解释、实际回答与提示历史。
- `ledger.md` 与 `records.json`，供检索、追溯与续读。

## 请求示例

### 单篇深读

```text
使用 $paper-research-mentor 深读附件论文。
先把科学问题、设计逻辑、关键公式和实验讲清楚，保存完整材料，
再挑一个能够检验我是否真的理解的问题与我讨论。
```

### 提炼写作素材

```text
从这篇文章提炼专业术语、常用搭配、句式和段落组织方式。
每条说明来源、论断强度、适用条件及如何换成我的研究内容。
不要直接把该文结果或贡献写成我的成果。
```

### 多篇综合和项目迁移

```text
比较这些论文，并只读取当前项目中与问题相关的 README、
数据说明和实验配置。给出维持基线、低成本借鉴和探索性改造，
写清最小验证实验、控制条件、资源成本与放弃标准。
```

### 自动完成、不进行实时提问

```text
自动完成全部分析，不要向我提问。
把思考题单独保存，所有未回答节点保持未验证。
```

### 继续讨论或补充资料

```text
继续上次的阅读。我对问题的实际回答是：……
请指出具体缺口，先给提示，再看是否需要完整解释。
```

```text
这是后来补充的项目说明和论文附录。
加入原有运行，保留讨论记录，重新核对相应结论和迁移建议。
```

## 脚本与记录接口

阅读分析由 Codex 完成；脚本不是离线自动论文理解模型。所有命令的 `--library` 参数放在子命令之前：

```bash
python paper-research-mentor/scripts/mentor.py --library ./paper-reading ingest ./paper.pdf
python paper-research-mentor/scripts/mentor.py --library ./paper-reading start --papers PAPER_ID
python paper-research-mentor/scripts/mentor.py --library ./paper-reading status --run RUN_ID
python paper-research-mentor/scripts/mentor.py --library ./paper-reading attach --run RUN_ID --papers NEW_SOURCE_ID
python paper-research-mentor/scripts/mentor.py --library ./paper-reading check --run RUN_ID
python paper-research-mentor/scripts/mentor.py --library ./paper-reading export --run RUN_ID
```

`PAPER_ID`、`RUN_ID` 使用命令返回的真实值。详见[完整记录契约](../paper-research-mentor/references/records-and-cli.md)。新增来源会保留已有事件和覆盖，同时使已完成状态降级以便重新检查；重复附加保持幂等。

不要把旧 MCP 的 `papers.db` 直接放入技能用户库。两者的数据结构不同，本次没有实现旧库迁移；需要时从原论文重新导入。

## 理解状态与使用边界

分析是否完成、证据核验程度和用户理解分别记录。没有回答是待参与；跳过仍未验证；看过提示或答案不能被记作同题独立掌握。用户可以随时要求直接解释，不需要强制考试。

用户的真实回答只能由对话实际内容记录。脚本能检查状态逻辑，不能证明一段字符串确实来自人，也不能替代对科学解释和学习效果的判断。原文中的命令或提示词只作为资料处理，不授权运行、上传或改写项目。
