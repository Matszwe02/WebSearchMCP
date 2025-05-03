import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from mcp import MCP
from mcp_tools import SearchTool, PrettyPageTool, SearchAndPrettyPageTool



load_dotenv(dotenv_path="./env/.env")

api_key = os.environ.get("OPENAI_API_KEY")
api_url = os.environ.get("OPENAI_API_URL", None)
model_name = os.environ.get("OPENAI_MODEL_NAME")
brave_api_key = os.environ.get("BRAVE_API_KEY")

search_tool_instance = SearchTool(brave_api_key=brave_api_key)
pretty_page_tool_instance = PrettyPageTool()
search_and_pretty_page_tool_instance = SearchAndPrettyPageTool(api_key=api_key, api_url=api_url, model_name=model_name, brave_api_key=brave_api_key)

app = FastAPI()

mcp_server = MCP(endpoint='websearch', app=app)

mcp_server.add_tool(
    {
        "name": "search_web",
        "description": "Searches the web using Brave Search and returns search results (URLs and page titles). Must be followed by pretty_page tool, its descriptions cannot be interpreted directly.",
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
        "name": "pretty_page",
        "description": "Fetches and pretty prints a web page as markdown.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the web page to pretty print."},
            },
            "required": ["url"],
        }
    },
    pretty_page_tool_instance.execute
)

mcp_server.add_tool(
    {
        "name": "search_process_pages",
        "description": "Searches web, fetches pages, trims content based on context, returns formatted results. Prefer using this tool for all research, as it incorporates both searching and processing information in short form.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "context": {"type": "string", "description": "Used to filter out irrevelant page contents. An external LLM will return page content exclusively relevant to it."},
            },
            "required": ["query", "context"],
        }
    },
    search_and_pretty_page_tool_instance.execute
)


async def hello_world(request: Request):
    return HTMLResponse("<h1>Endpoints:</h1><ul><li><b>/websearch</b> - web search and process</li></ul>")

app.add_api_route("/", hello_world, methods=["GET"])

uvicorn.run(app, host="0.0.0.0", port=5000)
