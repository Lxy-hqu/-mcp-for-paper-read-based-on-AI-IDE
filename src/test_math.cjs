const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");
const path = require("path");

async function main() {
  console.log("Starting MCP Client...");
  
  const transport = new StdioClientTransport({
    command: "node",
    args: [path.join(__dirname, "../dist/server.js")],
  });

  const client = new Client(
    { name: "test-client", version: "1.0.0" },
    { capabilities: {} }
  );

  await client.connect(transport);
  console.log("Connected to server.");

  const tools = await client.listTools();
  console.log("Available tools:", tools.tools.map(t => t.name));

  // Test Math Explainer
  console.log("\n--- Testing math_explainer ---");
  const sampleText = `
    The loss function is defined as $L = \\frac{1}{N} \\sum_{i=1}^N (y_i - \\hat{y}_i)^2$.
    where $N$ denotes the batch size, $y_i$ is the ground truth label, and $\\hat{y}_i$ represents the predicted value.
    We optimize this using SGD.
  `;
  
  const result = await client.callTool({
    name: "math_explainer",
    arguments: { text: sampleText }
  });
  
  const parsed = JSON.parse(result.content[0].text);
  console.log("Summary:\n", parsed.summary);

  await client.close();
}

main().catch(console.error);
