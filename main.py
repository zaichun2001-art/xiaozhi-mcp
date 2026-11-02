import asyncio
import os
import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types
from starlette.applications import Starlette
from starlette.routing import Mount, Route
import uvicorn

# MCP 서버 객체 생성
app = Server("xiaozhi-mcp")

# 1. 실시간 검색 도구(Tool) 목록 제공
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="web_search",
            description="Tavily를 이용하여 실시간 뉴스, 주식 시장 정보, 웹 정보를 검색합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 키워드 (예: 오늘 주식 시장, 최신 뉴스)"
                    }
                },
                "required": ["query"]
            }
        )
    ]

# 2. 샤오즈 AI가 검색을 호출할 때 Tavily API로 검색 수행
async def call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name == "web_search":
        if not arguments or "query" not in arguments:
            return [types.TextContent(type="text", text="검색어가 지정되지 않았습니다.")]
        
        query = arguments["query"]
        tavily_api_key = os.environ.get("TAVILY_API_KEY")
        
        if not tavily_api_key:
            return [types.TextContent(type="text", text="Render 환경 변수에 TAVILY_API_KEY가 설정되지 않았습니다.")]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_api_key, "query": query, "max_results": 5},
                    timeout=10.0
                )
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return [types.TextContent(type="text", text="관련된 검색 결과를 찾지 못했습니다.")]
                
                content = "\n\n".join([f"제목: {r.get('title')}\n출처: {r.get('url')}\n내용: {r.get('content')}" for r in results])
                return [types.TextContent(type="text", text=content)]
            except Exception as e:
                return [types.TextContent(type="text", text=f"검색 중 오류 발생: {str(e)}")]
                
    raise ValueError(f"Unknown tool: {name}")

# 도구 핸들러 연결 (set_logging_level 제거 완료)
app.list_tools = list_tools
app.call_tool = call_tool

# SSE 전송을 위한 Starlette 웹 앱 설정
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
