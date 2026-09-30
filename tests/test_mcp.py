"""Exercise the actual official SDK tool wrappers in memory."""

import asyncio
from ecuworkbench.server import mcp


def test_mcp_tool_inventory_and_read_only_annotations():
    tools = asyncio.run(mcp.list_tools())
    assert {tool.name for tool in tools} == {"capabilities", "inspect_tune", "compare_tunes", "summarize_log"}
    for tool in tools:
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.openWorldHint is False


def test_mcp_capability_tool_executes():
    result = asyncio.run(mcp.call_tool("capabilities", {}))
    content = result[0] if isinstance(result, tuple) else result
    assert content
