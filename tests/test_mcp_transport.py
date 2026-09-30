"""A real stdio process verifies MCP protocol compatibility, without a model."""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_actual_stdio_roundtrip_and_path_refusal(tmp_path):
    """Launch the real server, negotiate MCP, read a fixture and refuse escape."""
    root = tmp_path / "allowed"
    root.mkdir()
    (root / "sample.msq").write_text(
        '<msq><versionInfo signature="SYNTHETIC-FW" firmwareInfo="Synthetic display version"/><page number="1">'
        '<constant name="example" units="rpm">123</constant></page></msq>', encoding="utf-8")
    outside = tmp_path / "outside.msq"
    outside.write_text("private synthetic file", encoding="utf-8")

    async def exercise():
        parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "ecuworkbench"],
            env={**os.environ, "ECU_WORKBENCH_ROOT": str(root)},
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                inventory = await session.list_tools()
                assert len(inventory.tools) == 4
                description = await session.call_tool("capabilities", {})
                assert description.structuredContent["mode"] == "offline_read_only"
                inspected = await session.call_tool("inspect_tune", {"path": "sample.msq"})
                assert not inspected.isError
                assert inspected.structuredContent["firmware_signature"] == "SYNTHETIC-FW"
                assert inspected.structuredContent["firmware_info"] == "Synthetic display version"
                rejected = await session.call_tool("inspect_tune", {"path": "../outside.msq"})
                assert rejected.isError
                assert "private synthetic file" not in str(rejected)

    asyncio.run(exercise())
