from __future__ import annotations

import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_stdio_protocol_round_trip(knowledge_repo: Path) -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "skillhub.mcp_server", "--repo", str(knowledge_repo)],
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "search_knowledge",
                "get_knowledge",
                "list_knowledge",
                "recommend_knowledge",
            }

            search = await session.call_tool("search_knowledge", {"query": "security"})
            assert not search.isError
            assert search.structuredContent["results"][0]["id"] == "review"
            assert "content" not in search.structuredContent["results"][0]

            detail = await session.call_tool("get_knowledge", {"id": "review"})
            assert not detail.isError
            assert "authorization" in detail.structuredContent["content"]

            resource = await session.call_tool(
                "get_knowledge",
                {"id": "review", "resource": "references/checklist.md"},
            )
            assert not resource.isError
            assert "Verify access control" in resource.structuredContent["content"]

            source = knowledge_repo / "knowledge" / "skills" / "review" / "SKILL.md"
            updated = source.read_text(encoding="utf-8").replace(
                "input validation, and regression tests",
                "input validation, dependency risks, and updated regression tests",
            )
            source.write_text(updated, encoding="utf-8")

            refreshed = await session.call_tool("get_knowledge", {"id": "review"})
            assert not refreshed.isError
            assert "dependency risks" in refreshed.structuredContent["content"]
