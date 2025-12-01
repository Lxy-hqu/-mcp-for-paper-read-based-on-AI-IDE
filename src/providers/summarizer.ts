import { llm } from "../llm_client.js";
import { structureParser } from "./structure_parser.js";

export const summarizer = {
  definition: {
    name: "summarizer",
    description: "生成智能论文摘要或方法论概述（支持本地 LLM 加速）",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string", description: "论文全文或部分文本" },
        mode: {
          type: "string",
          enum: ["summary", "methodology", "layman"],
          description: "摘要模式：summary(标准摘要), methodology(方法论概述), layman(通俗解释)",
        },
      },
      required: ["text"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    const mode = input.mode || "summary";
    const text = input.text || "";

    // 1. 尝试结构化切分 (如果是全文)
    let sections: Record<string, string> = {};
    try {
      const structRes = await structureParser.handler({ text });
      sections = JSON.parse(structRes.content[0].text);
    } catch (e) {
      // Fallback if parsing fails or text is short
      sections = { "Full": text };
    }

    // 2. 准备上下文
    let context = "";
    if (mode === "summary") {
      // 优先使用 Abstract + Conclusion + Introduction
      context = (sections["Abstract"] || "") + "\n" + 
                (sections["Introduction"] || "").slice(0, 1000) + "\n" + 
                (sections["Conclusion"] || "");
      if (context.length < 100) context = text.slice(0, 2000); // Fallback
    } else if (mode === "methodology") {
      // 优先使用 Method
      context = sections["Method"] || sections["Proposed Method"] || sections["Methodology"] || "";
      if (!context) context = text.slice(0, 3000);
    } else {
      context = (sections["Abstract"] || "") + "\n" + (sections["Introduction"] || "").slice(0, 1000);
    }

    // 3. 尝试调用本地 LLM
    const isLLMAvailable = await llm.isAvailable();
    if (isLLMAvailable) {
      let prompt = "";
      if (mode === "summary") {
        prompt = `Please provide a concise academic summary of the following paper content:\n\n${context.slice(0, 4000)}`;
      } else if (mode === "methodology") {
        prompt = `Please summarize the key methodology and algorithms used in the following text. Focus on the technical details:\n\n${context.slice(0, 4000)}`;
      } else {
        prompt = `Explain the following scientific content in simple terms for a non-expert:\n\n${context.slice(0, 4000)}`;
      }

      const llmRes = await llm.chat(prompt, "You are a helpful research assistant.");
      if (llmRes) {
        return { content: [{ type: "text", text: `[AI Generated] ${llmRes}` }] };
      }
    }

    // 4. Fallback (Heuristic)
    let fallbackSummary = "";
    if (mode === "summary") {
      fallbackSummary = `[Local Extraction] 
**Abstract**: ${sections["Abstract"] || "Not found"}

**Conclusion Preview**: ${(sections["Conclusion"] || "").slice(0, 300)}...

(To get an AI summary, ensure a local LLM like Ollama is running on port 11434)`;
    } else if (mode === "methodology") {
      fallbackSummary = `[Local Extraction]
**Method Section Preview**:
${context.slice(0, 500)}...

(Key technical terms extracted: ${extractKeyTerms(context).join(", ")})`;
    } else {
      fallbackSummary = `[Local Extraction]
${(sections["Abstract"] || text).slice(0, 500)}...`;
    }

    return { content: [{ type: "text", text: fallbackSummary }] };
  },
};

function extractKeyTerms(text: string): string[] {
  // Simple heuristic to find capitalized phrases or math symbols
  const matches = text.match(/\b[A-Z][a-zA-Z]+\b/g) || [];
  return Array.from(new Set(matches)).slice(0, 10);
}
