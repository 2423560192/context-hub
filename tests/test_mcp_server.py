from pathlib import Path

from skillhub.mcp_server import create_server
from skillhub.service import KnowledgeService


def test_mcp_exposes_required_tools(knowledge_repo: Path) -> None:
    server = create_server(KnowledgeService(knowledge_repo))
    tool_names = set(server._tool_manager._tools)  # Intentional smoke test of registered adapter surface.
    assert tool_names == {
        "search_knowledge",
        "get_knowledge",
        "list_knowledge",
        "recommend_knowledge",
    }

