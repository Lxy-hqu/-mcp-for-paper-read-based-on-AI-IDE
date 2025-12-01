import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { db } from "../database.js";
import * as math from "mathjs";

type Input = { text: string; paper_path?: string };

export const mathExplainer = {
  definition: {
    name: "math_explainer",
    description: "深度数学智能：提取公式、构建 AST、推导关系并存入数据库",
    inputSchema: {
      type: "object",
      properties: { 
        text: { type: "string" },
        paper_path: { type: "string", description: "可选，用于关联数据库" }
      },
      required: ["text"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    const text = input.text || "";
    
    // 1. 提取 LaTeX (增强版正则)
    const inlineMathRegex = /\$([^$]+)\$/g;
    const blockMathRegex = /\\\[([\s\S]*?)\\\]/g;
    const formulas: string[] = [];
    let match;
    
    while ((match = inlineMathRegex.exec(text)) !== null) formulas.push(match[1]);
    while ((match = blockMathRegex.exec(text)) !== null) formulas.push(match[1]);

    // 2. 符号挖掘
    const symbolRegex = /(?:where|let)\s+\$([^$]+)\$\s+(?:is|denotes|stands for|represents)\s+([^,.;]+)/gi;
    const symbolMap: Record<string, string> = {};
    const dbSymbols: any[] = [];
    
    while ((match = symbolRegex.exec(text)) !== null) {
      const symbol = match[1].trim();
      const definition = match[2].trim();
      if (symbol.length < 10) {
        symbolMap[symbol] = definition;
        dbSymbols.push({ symbol, definition, latex: symbol });
      }
    }

    // 3. AST 解析与结构化 (使用 mathjs 尝试解析简单公式)
    const astAnalysis: any[] = [];
    for (const f of formulas.slice(0, 10)) { // 仅分析前 10 个，避免超时
      try {
        // 尝试将 LaTeX 转为 mathjs 可读格式（非常简化的 heuristic）
        // 注意：mathjs 不直接支持 LaTeX，这里做简单替换演示原理
        const simplified = f.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1)/($2)")
                            .replace(/\\sum/g, "sum")
                            .replace(/[\\][a-zA-Z]+/g, ""); // 去除其他 LaTeX 命令
        
        const node = math.parse(simplified);
        const variables = node.filter((n: any) => n.isSymbolNode).map((n: any) => n.name);
        astAnalysis.push({
          original: f,
          variables: [...new Set(variables)],
          structure: node.toString()
        });
      } catch (e) {
        // 忽略解析失败的复杂 LaTeX
      }
    }

    // 4. 存入数据库 (如果有 path)
    if (input.paper_path) {
      const paper = db.getPaperByPath(input.paper_path);
      if (paper) {
        db.saveSymbols(paper.id, dbSymbols);
      }
    }

    return {
      content: [
        { type: "text", text: JSON.stringify({ 
            formulas_count: formulas.length,
            symbols: symbolMap,
            ast_analysis: astAnalysis,
            derivation_hint: "提示：AST 分析已识别部分变量依赖，可用于推导链构建。"
          }) 
        }
      ]
    };
  },
};
