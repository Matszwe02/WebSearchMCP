import os
import logging
from mcp.server.sse import SseServerTransport
from mcp.server.lowlevel import Server
from mcp.types import Tool, TextContent
from mcp_tools import SearchTool, PrettyPageTool, SearchAndPrettyPageTool
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

server = Server("web_search_mcp")

search_tool_instance = SearchTool(brave_api_key=os.environ.get("BRAVE_API_KEY"))
pretty_page_tool_instance = PrettyPageTool()
search_and_pretty_page_tool_instance = SearchAndPrettyPageTool(brave_api_key=os.environ.get("BRAVE_API_KEY"))


SEARCH_WEB_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "The search query."},
    },
    "required": ["query"],
}
PRETTY_PAGE_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "The URL of the web page to pretty print."},
    },
    "required": ["url"],
}
SEARCH_PROCESS_PAGES_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "The search query."},
        "context": {"type": "string", "description": "Context for trimming page content. Must be very descriptive, only parts mathing it will be returned"},
    },
    "required": ["query", "context"],
}


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_web",
            description="Searches the web using Brave Search and returns search results.",
            inputSchema=SEARCH_WEB_INPUT_SCHEMA
        ),
        Tool(
            name="pretty_page",
            description="Fetches and pretty prints a web page as markdown.",
            inputSchema=PRETTY_PAGE_INPUT_SCHEMA
        ),
        Tool(
            name="search_process_pages",
            description="Searches web, fetches pages, trims content based on context, returns formatted results.",
            inputSchema=SEARCH_PROCESS_PAGES_INPUT_SCHEMA
        )
    ]


@server.call_tool()
async def handle_tool_call(name: str, arguments: dict[str, str]) -> list[TextContent]:
        
    if name == "search_web":
        query = arguments.get("query")
        if not query:
            return [TextContent(type="text", text="Error: Missing search query.")]
        try:
            return [TextContent(type="text", text=search_tool_instance.execute(query))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error during web search: {e}")]
    
    elif name == "pretty_page":
        url = arguments.get("url")
        if not url:
            return [TextContent(type="text", text="Error: Missing URL parameter.")]
        try:
            return [TextContent(type="text", text=pretty_page_tool_instance.execute(url))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error processing URL '{url}' in pretty_page tool: {e}")]
    
    elif name == "search_process_pages":
        query = arguments.get("query")
        context = arguments.get("context")
        if not query or not context:
            return [TextContent(type="text", text="Error: Missing query or context parameter.")]
        try:
            return [TextContent(type="text", text=search_and_pretty_page_tool_instance.execute(query, context))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error during search_process_pages: {e}")]
    
    else:
        logging.warning(f"Unknown tool name received: {name}")
        return [TextContent(type="text", text=f"Error: Unknown tool name '{name}'")]



if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.requests import Request
    MESSAGE_ENDPOINT_PATH = "/mcp_messages/"
    sse_transport = SseServerTransport(MESSAGE_ENDPOINT_PATH)
    
    async def handle_sse_connection(request: Request):
        async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
    
    routes = [Route("/", endpoint=handle_sse_connection, methods=["GET"]), Mount(MESSAGE_ENDPOINT_PATH, app=sse_transport.handle_post_message)]
    
    app = Starlette(routes = routes)
    uvicorn.run(app, port=8000)
