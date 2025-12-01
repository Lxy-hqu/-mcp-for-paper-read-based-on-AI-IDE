const { Client } = require("@modelcontextprotocol/sdk/client/index.js");
const { StdioClientTransport } = require("@modelcontextprotocol/sdk/client/stdio.js");
const { spawn } = require("child_process");
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

  // Test pdf_loader if a PDF exists, otherwise just skip
  // We don't have a PDF here, so we just check listTools
  
  await client.close();
}

main().catch(console.error);
