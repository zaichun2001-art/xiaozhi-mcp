import asyncio
import os
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Mount, Route
import uvicorn

app = Server("xiaozhi-mcp")

# 1. 샤오즈 AI가 사용할 수 있는 검색 도구(Tool) 목록 등록
@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description="Search the web for real-time information, news, and stock market data using Tavily.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for looking up stock prices or market info."
                    }
                },
                "required": ["query"]
            }
        )
    ]

# 2. 샤오즈 AI가 검색을 요청했을 때 Tavily API를 호출하는 로직
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "web_search":
        query = arguments.get("query")
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        
        if not tavily_api_key:
            return [TextContent(type="text", text="Tavily API 키가 설정되지 않았습니다.")]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_api_key, "query": query, "max_results": 3},
                    timeout=10.0
                )
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return [TextContent(type="text", text="관련된 검색 결과를 찾지 못했습니다.")]
                
                content = "\n\n".join([f"출처: {r.get('url')}\n내용: {r.get('content')}" for r in results])
                return [TextContent(type="text", text=content)]
            except Exception as e:
                return [TextContent(type="text", text=f"검색 중 오류가 발생했습니다: {str(e)}")]
                
    raise ValueError(f"Unknown tool: {name}")

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
