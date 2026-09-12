"""Phase 2: read-only MCP tool surface (allowlist parsing, gating, wiring)."""

from types import SimpleNamespace

import pytest

pytest.importorskip("strands", reason="strands-agents is not installed")

from tests.test_auth import make_user  # noqa: E402,F401


def _patch_mcp_settings(monkeypatch, url=None, allowed=None):
    import app.services.outreach_mcp as mcp_module

    monkeypatch.setattr(
        mcp_module,
        "settings",
        SimpleNamespace(mcp_server_url=url, mcp_allowed_tools=allowed),
    )
    return mcp_module


def test_parse_tool_allowlist_splits_and_trims():
    from app.services.outreach_mcp import parse_tool_allowlist

    assert parse_tool_allowlist(" get_events , lookup_breaks ") == [
        "get_events",
        "lookup_breaks",
    ]
    assert parse_tool_allowlist("") == []
    assert parse_tool_allowlist(None) == []
    assert parse_tool_allowlist(" , , ") == []


def test_mcp_enabled_requires_url_and_allowlist(monkeypatch):
    module = _patch_mcp_settings(monkeypatch, url="http://calendar.local/mcp")

    assert module.mcp_enabled() is False

    _patch_mcp_settings(
        monkeypatch,
        url="http://calendar.local/mcp",
        allowed="get_events",
    )
    assert module.mcp_enabled() is True

    _patch_mcp_settings(monkeypatch, url=None, allowed="get_events")
    assert module.mcp_enabled() is False


def test_build_tool_filters_uses_allowlist():
    from app.services.outreach_mcp import build_tool_filters

    filters = build_tool_filters(["get_events", "lookup_breaks"])
    assert filters["allowed"] == ["get_events", "lookup_breaks"]


class _FakeMcpTool:
    def __init__(self, name):
        self.tool_name = name


def test_readonly_mcp_tools_yields_nothing_when_disabled(monkeypatch):
    module = _patch_mcp_settings(monkeypatch, url=None, allowed=None)

    with module.ReadonlyMcpTools() as mcp:
        assert mcp.tools == []


def test_readonly_mcp_tools_degrades_when_server_fails(monkeypatch):
    module = _patch_mcp_settings(
        monkeypatch, url="http://calendar.local/mcp", allowed="get_events"
    )

    class _ExplodingClient:
        def __init__(self, *args, **kwargs):
            raise OSError("connection refused")

    import strands.tools.mcp as strands_mcp

    monkeypatch.setattr(strands_mcp, "MCPClient", _ExplodingClient)
    with module.ReadonlyMcpTools() as mcp:
        assert mcp.tools == []


def test_qa_agent_receives_allowlisted_mcp_tools(monkeypatch, client, make_user, make_student):
    import app.services.outreach_qa as qa_module
    import app.services.outreach_mcp as mcp_module

    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    make_student(headers=headers)

    captured = {}

    def fake_build(tools, model=None, owner_id=None, session_manager=None, conversation_manager=None):
        from app.services.outreach_plan_agent import build_outreach_qa_agent
        from tests.fake_strands_model import FakeModel

        captured["tool_names"] = [
            getattr(tool, "tool_name", getattr(tool, "__name__", str(tool)))
            for tool in tools
        ]
        return build_outreach_qa_agent(
            tools,
            model=FakeModel(turns=[{"type": "text", "text": "Because of the follow-up."}]),
            owner_id=owner_id,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
        )

    monkeypatch.setattr(qa_module, "build_outreach_qa_agent", fake_build)

    class _FakeReadonly:
        def __enter__(self):
            self.tools = [_FakeMcpTool("mcp_school_get_events")]
            return self

        def __exit__(self, *exc):
            self.tools = []

    monkeypatch.setattr(qa_module, "ReadonlyMcpTools", _FakeReadonly)
    monkeypatch.setattr(
        "app.api.v1.outreach_conversations.settings",
        SimpleNamespace(bedrock_model_id="test-model"),
    )

    response = client.post(
        "/api/v1/outreach-plan/ask",
        json={"question": "Any school breaks coming up?"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert "mcp_school_get_events" in captured["tool_names"]
    assert "get_outreach_candidates" in captured["tool_names"]
