import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server

# MCP 서버 초기화
app = Server("xiaozhi-mcp")

@app.list_tools()
async def handle_list_tools() -> list:
    return []

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
