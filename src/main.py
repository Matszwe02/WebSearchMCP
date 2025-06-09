import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from mcp import MCP
from mcp_tools import SearchTool, PrintPageTool, SearchAndPrintPageTool



load_dotenv(dotenv_path="./env/.env")

api_key = os.environ.get("OPENAI_API_KEY")
api_url = os.environ.get("OPENAI_API_URL", None)
model_name = os.environ.get("OPENAI_MODEL_NAME")
brave_api_key = os.environ.get("BRAVE_API_KEY")
proxy = os.environ.get("PROXY", None)

search_tool_instance = SearchTool(brave_api_key=brave_api_key)
print_page_tool_instance = PrintPageTool(proxy)

app = FastAPI()

mcp_server = MCP(app=app)

mcp_server.add_tool(
    {
        "name": "search_web",
        "description": "Searches the web using Brave Search and returns search results (URLs and page titles). Must be followed by print_page tool, its descriptions cannot be interpreted directly, as it contains only references to actual data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
            },
            "required": ["query"],
        }
    },
    search_tool_instance.execute
)

mcp_server.add_tool(
    {
        "name": "print_page",
        "description": "Fetches and prints a web page as markdown.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the web page to print."},
            },
            "required": ["url"],
        }
    },
    print_page_tool_instance.execute
)

if api_key and model_name:
    search_and_print_page_tool_instance = SearchAndPrintPageTool(api_key, api_url, model_name, brave_api_key, proxy)
    mcp_server.add_tool(
        {
            "name": "search_process_pages",
            "description": "Searches web, fetches pages, trims content based on context, returns formatted results. Prefer using this tool for all research, as it incorporates both searching and processing information in short form, minimising context usage.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."},
                    "context": {"type": "string", "description": "Used to filter out irrevelant page contents. An external LLM will return page content exclusively relevant to it."},
                },
                "required": ["query", "context"],
            }
        },
        search_and_print_page_tool_instance.execute
    )

uvicorn.run(app, host="0.0.0.0", port=5000)
