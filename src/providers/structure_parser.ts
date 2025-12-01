export const structureParser = {
  definition: {
    name: "structure_parser",
    description: "对论文文本进行章节切分与结构化提取",
    inputSchema: {
      type: "object",
      properties: { text: { type: "string" } },
      required: ["text"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    const sections: Record<string, string> = {};
    const keywords = [
      "Abstract",
      "Introduction",
      "Related Work",
      "Method",
      "Experiments",
      "Conclusion",
      "References",
    ];
    let currentSection = "Header";
    let buffer: string[] = [];

    const lines = (input.text || "").split("\n");
    for (const line of lines) {
      const trimLine = line.trim();
      const match = keywords.find(
        (k) =>
          trimLine.toLowerCase().startsWith(k.toLowerCase()) &&
          trimLine.length < 50
      );
      if (match) {
        if (buffer.length > 0) {
          sections[currentSection] = buffer.join("\n");
        }
        currentSection = match;
        buffer = [];
      } else {
        buffer.push(line);
      }
    }
    if (buffer.length > 0) {
      sections[currentSection] = buffer.join("\n");
    }

    return { content: [{ type: "text", text: JSON.stringify(sections) }] };
  },
};
