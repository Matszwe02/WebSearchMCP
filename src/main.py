import logging
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.requests import Request
from starlette.responses import HTMLResponse
import mcp_server


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def hello_world(request: Request):
    return HTMLResponse("<h1>Endpoints:</h1><ul><li><b>/websearch</b> - web search and process</li></ul>")

routes = [
    Route("/", endpoint=hello_world, methods=["GET"])
]

routes.extend(mcp_server.routes)

app = Starlette(routes = routes)
uvicorn.run(app, host="0.0.0.0", port=5000)
