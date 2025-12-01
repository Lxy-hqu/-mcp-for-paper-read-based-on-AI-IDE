import { Server } from "@modelcontextprotocol/sdk/server/index.js";

type Input = { 
  type: "flowchart" | "dependency_graph";
  data: string; 
};

export const visualization = {
  definition: {
    name: "visualization",
    description: "生成 Mermaid 流程图或变量依赖图代码",
    inputSchema: {
      type: "object",
      properties: { 
        type: { type: "string", enum: ["flowchart", "dependency_graph"] },
        data: { type: "string", description: "用于生成图表的结构化描述或 JSON" }
      },
      required: ["type", "data"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    let mermaidCode = "";
    
    if (input.type === "flowchart") {
      // 假设 input.data 是步骤列表的文本
      const steps = input.data.split("\n").filter((s: string) => s.trim().length > 0);
      mermaidCode = `
graph TD
  Start([Start]) --> ${steps.map((s: string, i: number) => `Step${i}[${s.slice(0, 20)}...]`).join(" --> ")}
  Step${steps.length - 1} --> End([End])
      `;
    } else {
      // 依赖图
      mermaidCode = `
graph LR
  L[Loss Function] --> y_hat[Prediction]
  y_hat --> Model[Model Architecture]
  Model --> Input[Input Data]
  L --> y[Ground Truth]
      `;
    }

    return { 
      content: [
        { type: "text", text: mermaidCode.trim() },
        { type: "text", text: "\n\n(提示：将此代码粘贴到 Mermaid Live Editor 或 Markdown 中查看)" }
      ] 
    };
  },
};
