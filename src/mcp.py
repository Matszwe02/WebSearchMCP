import json
import uuid
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse



class MCP:
    def __init__(self, app: FastAPI, endpoint = ""):
        self.endpoint = endpoint.strip('/')
        if self.endpoint: self.endpoint = '/' + self.endpoint
        self.app = app
        self.tools = []
        self.active_sse_connections = {}
        
        # idk what happens with that
        self.app.add_api_route(f"{self.endpoint}", self.sse_endpoint)
        self.app.add_api_route(f"{self.endpoint}/sse", self.sse_endpoint)
        self.app.add_api_route(f"{self.endpoint}/messages", self.post_handler, methods=["POST"], name="post_handler")
        self.app.add_api_route(f"/{self.endpoint}", self.sse_endpoint)
        self.app.add_api_route(f"/{self.endpoint}/sse", self.sse_endpoint)
        self.app.add_api_route(f"/{self.endpoint}/messages", self.post_handler, methods=["POST"], name="post_handler")
        self.app.add_api_route(f"//{self.endpoint}", self.sse_endpoint)
        self.app.add_api_route(f"//{self.endpoint}/sse", self.sse_endpoint)
        self.app.add_api_route(f"//{self.endpoint}/messages", self.post_handler, methods=["POST"], name="post_handler")


    def add_tool(self, tool_dict, tool_method):
        self.tools.append({"tool_dict": tool_dict, "tool_method": tool_method})


    async def sse_endpoint(self, request: Request):
        print(f"Endpoint /{self.endpoint}/sse called")
        session_id = str(uuid.uuid4())
        message_queue = asyncio.Queue()
        self.active_sse_connections[session_id] = message_queue
        
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        host = request.headers.get("Host")
        
        if forwarded_proto and host:
            base_url = f"{forwarded_proto}://{host}"
        else:
            base_url = str(request.base_url)
        
        messages_url = f"{base_url}/{self.endpoint}/messages?session_id={session_id}"
        
        async def event_generator(messages_url):
            message_queue = self.active_sse_connections.get(session_id)
            if not message_queue:
                return
            
            await asyncio.sleep(0.1)
            
            yield {
                "event": "endpoint",
                "data": str(messages_url)
            }
            
            yield {"event": "ping", "data": "Server is alive!"}
            
            while True:
                try:
                    message = await asyncio.wait_for(message_queue.get(), timeout=30)
                    yield message
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "Server is alive!"}
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    yield {"event": "error", "data": f"Server error: {e}"}
                    break
        
        return EventSourceResponse(event_generator(messages_url))


    async def post_handler(self, request: Request, session_id: str):
        print(f"Endpoint /{self.endpoint}/messages called for session_id: {session_id}")
        message_queue = self.active_sse_connections.get(session_id)
        if not message_queue:
            raise HTTPException(status_code=404, detail="Session not found")
        
        try:
            body = await request.json()
            method = body.get("method")
            params = body.get("params", {})
            request_id = body.get("id", None)
            response = None
            error = None
            
            try:
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {"listTools": True, "callTool": True},
                                "resources": {}
                            },
                            "serverInfo": {"name": "PyMCP", "version": "1.0.0"}
                        }
                    }
                
                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": [tool["tool_dict"] for tool in self.tools]}
                    }
                
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    tool_result = None
                    tool_method = None
                    
                    for tool in self.tools:
                        if tool["tool_dict"]["name"] == tool_name:
                            tool_method = tool["tool_method"]
                            break
                    
                    if tool_method:
                        try:
                            tool_result = tool_method(**arguments)
                        except Exception as e:
                            error = {"code": -32603, "message": f"Internal error during tool execution: {e}"}
                    else:
                        error = {"code": -32601, "message": f"Method '{tool_name}' not found"}
                    
                    if error:
                         response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": error
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": tool_result or ""
                                    }
                                ]
                            }
                        }
                
                elif method == "resources/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"resources": []}
                    }
                
                elif method == "resources/templates/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"resourceTemplates": []}
                    }
                
                else:
                    error = {"code": -32601, "message": f"Method '{method}' not found"}
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": error
                    }
            
            except Exception as e:
                error = {"code": -32603, "message": f"Internal error processing method: {e}"}
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": error
                }
            
            if response and request_id is not None:
                sse_event = {
                    "event": "message",
                    "data": json.dumps(response)
                }
                await message_queue.put(sse_event)
            elif response and request_id is None:
                pass
            
            return JSONResponse({"status": "Message received and processed"})
        
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error: Invalid JSON was received by the server."}
            }
            if message_queue:
                 await message_queue.put({"event": "error", "data": json.dumps(error_response)})
            return JSONResponse(error_response, status_code=400)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {e}"}
            }
            if message_queue:
                 await message_queue.put({"event": "error", "data": json.dumps(error_response)})
            return JSONResponse(error_response, status_code=500)
