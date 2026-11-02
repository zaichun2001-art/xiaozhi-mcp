import os
import subprocess

endpoint = os.environ.get("MCP_ENDPOINT")
api_key = os.environ.get("TAVILY_API_KEY")

if endpoint and api_key:
    cmd = f"npx -y @modelcontextprotocol/server-tavily --api-key {api_key}"
    subprocess.run(f"python -m mcp_pipe {endpoint} -- {cmd}", shell=True)