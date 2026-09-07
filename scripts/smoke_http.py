"""Protocol-level smoke test for a running SkillHub Streamable HTTP server."""

from __future__ import annotations

import argparse
import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def check(url: str, query: str) -> None:
    async with streamable_http_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            tools = await session.list_tools()
            result = await session.call_tool("search_knowledge", {"query": query})
            print("tools:", ", ".join(tool.name for tool in tools.tools))
            print("search result:", result.structuredContent)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    parser.add_argument("--query", default="code review")
    args = parser.parse_args()
    asyncio.run(check(args.url, args.query))


if __name__ == "__main__":
    main()

