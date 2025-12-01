import { Server } from "@modelcontextprotocol/sdk/server/index.js";

type Input = { 
  task_type: "pytorch_model" | "training_loop" | "config_yaml";
  context: string; 
};

export const codeGenerator = {
  definition: {
    name: "code_generator",
    description: "从论文描述生成 PyTorch 代码框架、训练循环或配置文件",
    inputSchema: {
      type: "object",
      properties: { 
        task_type: { type: "string", enum: ["pytorch_model", "training_loop", "config_yaml"] },
        context: { type: "string", description: "包含超参数、模型结构的文本片段" }
      },
      required: ["task_type", "context"],
      additionalProperties: false,
    },
  },
  handler: async (input: any) => {
    const { task_type, context } = input;
    let code = "";

    // 1. 简单的参数提取 (Heuristic)
    const lrMatch = context.match(/learning rate (?:of )?([\d.e-]+)/i);
    const batchMatch = context.match(/batch size (?:of )?(\d+)/i);
    const epochsMatch = context.match(/(\d+) epochs/i);
    
    const params = {
      lr: lrMatch ? parseFloat(lrMatch[1]) : 0.001,
      batch_size: batchMatch ? parseInt(batchMatch[1]) : 32,
      epochs: epochsMatch ? parseInt(epochsMatch[1]) : 100
    };

    if (task_type === "pytorch_model") {
      code = `
import torch
import torch.nn as nn

class PaperModel(nn.Module):
    def __init__(self):
        super(PaperModel, self).__init__()
        # TODO: 根据论文描述填充层
        # Context hint: ${context.slice(0, 100)}...
        self.layer1 = nn.Linear(784, 128)
        self.relu = nn.ReLU()
        self.output = nn.Linear(128, 10)
    
    def forward(self, x):
        x = self.layer1(x)
        x = self.relu(x)
        return self.output(x)
      `;
    } else if (task_type === "training_loop") {
      code = `
import torch
import torch.optim as optim

# Hyperparameters extracted from paper
lr = ${params.lr}
batch_size = ${params.batch_size}
epochs = ${params.epochs}

model = PaperModel()
optimizer = optim.Adam(model.parameters(), lr=lr)
criterion = nn.CrossEntropyLoss()

for epoch in range(epochs):
    # Training loop template
    pass
      `;
    } else if (task_type === "config_yaml") {
      code = `
# Generated Config based on Paper
training:
  lr: ${params.lr}
  batch_size: ${params.batch_size}
  epochs: ${params.epochs}
  optimizer: "Adam"
  seed: 42

data:
  dataset_path: "./data"
  num_workers: 4
      `;
    }

    return { content: [{ type: "text", text: code.trim() }] };
  },
};
