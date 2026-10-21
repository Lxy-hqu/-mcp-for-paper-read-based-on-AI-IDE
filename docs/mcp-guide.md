# 原 MCP：安装与兼容说明

[项目首页](../README.zh-CN.md) · [Codex Skill 用法](usage.md)

原 TypeScript MCP 保留在 `src/`，适用于需要 STDIO 工具接口的客户端。Codex 使用 `paper-research-mentor/` 技能时不要求先运行这个服务。本次发布新增技能和文档，没有修复或重新验证原 MCP 的全部调用链。

## 环境和启动

需要 Node.js、npm、Git，以及能安装 `better-sqlite3` 原生依赖的环境。当前锁文件的 `better-sqlite3` 声明 Node.js 为 `20.x || 22.x || 23.x || 24.x || 25.x`；这纠正了旧 README 的 Node.js 16+ 说明。以实际锁文件与依赖安装检查为准。

在仓库根目录执行：

```bash
npm install
npx tsc
```

客户端启动命令为 Node.js，参数为编译后的 `dist/server.js` 的绝对路径。Windows 配置示例：

```json
{
  "mcpServers": {
    "local-papers": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": ["C:\\path\\to\\repository\\dist\\server.js"],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

请替换为本机路径；不同客户端的配置入口和字段可能不同，以上对应仓库原有模板。重连后可先调用 `pdf_loader`，参数为 `{"paths":["C:\\path\\paper.pdf"]}`。也可使用仓库的 `npm start` 启动 TypeScript 入口，但客户端启动方式须避免向 STDIO 协议输出多余文本。

## 实现能力与已知限制

| 工具 | 实际实现 |
|---|---|
| `pdf_loader` | 使用 pdf-parse 提取本地文本、页数及文件元数据，不含 OCR |
| `structure_parser` | 按固定英文标题规则切分，不等于通用版面理解 |
| `summarizer` | 可选请求本地 Ollama；不可用时返回规则摘录，不代表经过深层理解的摘要 |
| `math_explainer` | 正则提取与简化 mathjs 解析，最多尝试前10个公式，不是完整 LaTeX 推导系统 |
| `code_generator` | 少量超参数匹配加固定骨架，不是忠实论文复现 |
| `visualization` | 按输入行生成流程图；依赖图使用固定模板 |
| `generate_report` | 存在可视化入参及数学输出字段不一致，当前可能在报告落盘前报错 |

`generate_report` 向可视化传 `text`，而工具读取 `data`；数学部分消费的字段也与数学工具返回不同。数据库存在论文/符号/实验表，但目前正常阅读入口未形成完整自动入库与检索流程。旧的验证脚本对报告主要检查不存在文件的错误处理，不能据此声称真实论文报告链路已通过。

## Ollama 与本地处理

原客户端默认请求 `127.0.0.1:11434` 的 `llama3`。它要求本机已有相应服务和模型，仓库不会自动部署。PDF解析或数据库位于本机，并不意味着客户端宿主大模型也在本机推理。

## 多机与数据

在目标机器重新安装依赖、重新编译并调整绝对路径。原生模块不适合直接跨系统复制。原 MCP 根据进程工作目录决定 `papers.db` 的位置；迁移前确认实际数据目录。请备份自己的数据，不要将旧 MCP 数据库与新技能用户库混用。
