def test_server_has_analyze_western_blot_tool():
    import server
    tools = server.mcp._tool_manager.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "analyze_western_blot" in tool_names


def test_tool_requires_image_source():
    import server
    tools = {t.name: t for t in server.mcp._tool_manager.list_tools()}
    tool = tools["analyze_western_blot"]
    assert "image_source" in tool.parameters["properties"]
    assert "image_source" in tool.parameters.get("required", [])
