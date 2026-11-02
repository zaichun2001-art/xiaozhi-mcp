import asyncio
import os
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
import uvicorn

app = Server("xiaozhi-mcp")

# SSE 전송을 위한 Starlette 앱 설정
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0],
            streams[1],
            app.create_initialization_options()
        )

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
