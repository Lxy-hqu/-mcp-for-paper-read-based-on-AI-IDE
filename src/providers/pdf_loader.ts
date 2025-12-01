import fs from "fs/promises";
import pdfParse from "pdf-parse";

export const pdfLoader = {
  definition: {
    name: "pdf_loader",
    description: "读取本地 PDF，解析文本与元数据",
    inputSchema: {
      type: "object",
      properties: { paths: { type: "array", items: { type: "string" } } },
      required: ["paths"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    const results: any[] = [];
    const paths = input.paths || [];
    for (const p of paths) {
      try {
        const buf = await fs.readFile(p);
        const data = await pdfParse(buf);
        const meta = data.info || {};
        results.push({
          path: p,
          title: meta.Title || null,
          author: meta.Author || null,
          pages: data.numpages,
          text: data.text,
        });
      } catch (e: any) {
        results.push({ path: p, error: String(e) });
      }
    }
    return { content: [{ type: "text", text: JSON.stringify({ results }) }] };
  },
};
