import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { pdfLoader } from "./providers/pdf_loader.js";
import { structureParser } from "./providers/structure_parser.js";
import { summarizer } from "./providers/summarizer.js";
import { mathExplainer } from "./providers/math_explainer.js";
import { codeGenerator } from "./providers/code_generator.js";
import { visualization } from "./providers/visualization.js";
import { reportGenerator } from "./providers/report_generator.js";

// Registry
const tools = [
  pdfLoader, 
  structureParser, 
  summarizer, 
  mathExplainer,
  codeGenerator,
  visualization,
  reportGenerator
];

const server = new Server(
  {
    name: "mcp-local-papers",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: tools.map((t) => t.definition),
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = tools.find((t) => t.definition.name === request.params.name);
  if (!tool) {
    throw new Error(`Tool not found: ${request.params.name}`);
  }
  return tool.handler(request.params.arguments);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

run().catch((error) => {
  console.error("Fatal error running server:", error);
  process.exit(1);
});
