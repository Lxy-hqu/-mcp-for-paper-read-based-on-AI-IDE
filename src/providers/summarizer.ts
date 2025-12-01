export const summarizer = {
  definition: {
    name: "summarizer",
    description: "生成论文摘要（纯本地逻辑）",
    inputSchema: {
      type: "object",
      properties: {
        text: { type: "string" },
        mode: {
          type: "string",
          enum: ["one-sentence", "bullet", "beginner"],
          description: "摘要模式",
        },
      },
      required: ["text"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    const mode = input.mode || "one-sentence";
    let summary = "";
    if (mode === "one-sentence") {
      summary = `（本地模拟摘要）本文探讨了... ${input.text.slice(0, 30)}...`;
    } else if (mode === "bullet") {
      summary = `- 要点1：${input.text.slice(0, 15)}...\n- 要点2：...`;
    } else {
      summary = `通俗解释：...`;
    }
    return { content: [{ type: "text", text: summary }] };
  },
};
