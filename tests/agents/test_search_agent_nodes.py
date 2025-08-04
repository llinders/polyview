import json
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import pytest

from polyview.agents.search_agent import (
    process_results_node,
    should_continue,
    tool_node,
)
from polyview.core.state import State


@pytest.fixture
def empty_state() -> State:
    """Provides a fresh, empty state for testing initial conditions."""
    return {
        "messages": [],
        "topic": "",
        "raw_articles": [],
        "article_perspectives": [],
        "consolidated_perspectives": [],
        "final_perspectives": [],
        "summary": "",
        "iteration": 0,
        "missing_perspectives": [],
    }


@pytest.fixture
def state_with_tool_messages(empty_state: State) -> State:
    """Creates a state object with sample tool messages containing search results."""
    search_results_1 = [
        {"url": "http://a.com", "title": "A", "content": "Content A", "score": 0.9},
        {"url": "http://b.com", "title": "B", "content": "Content B", "score": 0.8},
    ]
    search_results_2 = [
        {"url": "http://c.com", "title": "C", "content": "Content C", "score": 0.95},
    ]

    messages = [
        HumanMessage(content="Initial research prompt."),
        ToolMessage(content=json.dumps(search_results_1), tool_call_id="call_1"),
        ToolMessage(content=json.dumps(search_results_2), tool_call_id="call_2"),
    ]

    state = empty_state.copy()
    state.update(
        {
            "messages": messages,
            "topic": "climate change",
        }
    )
    return state


class TestToolNode:
    @patch("polyview.agents.search_agent.search_tool")
    def test_returns_empty_list_when_no_tool_calls_are_present(
        self, mock_search_tool, empty_state
    ):
        state = empty_state
        state["messages"] = [AIMessage(content="No tools needed.")]
        result = tool_node(state)
        assert result["messages"] == []
        mock_search_tool.invoke.assert_not_called()

    @patch("polyview.agents.search_agent.search_tool")
    def test_correctly_handles_multiple_tool_calls(self, mock_search_tool, empty_state):
        mock_search_tool.invoke.side_effect = [
            {"results": [{"url": "http://a.com", "score": 0.9}]},
            {"results": [{"url": "http://b.com", "score": 0.8}]},
        ]
        tool_calls = [
            {"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}},
            {"id": "call_2", "name": "tavily_search", "args": {"query": "q2"}},
        ]
        state = empty_state
        state["messages"] = [AIMessage(content="", tool_calls=tool_calls)]

        result = tool_node(state)
        assert len(result["messages"]) == 2
        assert json.loads(result["messages"][0].content)[0]["url"] == "http://a.com"
        assert json.loads(result["messages"][1].content)[0]["url"] == "http://b.com"

    @patch("polyview.agents.search_agent.search_tool")
    def test_gracefully_handles_tool_failure(self, mock_search_tool, empty_state):
        mock_search_tool.invoke.side_effect = Exception("API limit reached")
        tool_calls = [
            {"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}}
        ]
        state = empty_state
        state["messages"] = [AIMessage(content="", tool_calls=tool_calls)]

        result = tool_node(state)
        assert len(result["messages"]) == 1
        error_content = json.loads(result["messages"][0].content)
        assert "error" in error_content
        assert error_content["error"] == "API limit reached"

    @patch("polyview.agents.search_agent.search_tool")
    def test_handles_empty_search_results(self, mock_search_tool, empty_state):
        mock_search_tool.invoke.return_value = {"results": []}
        tool_calls = [
            {"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}}
        ]
        state = empty_state
        state["messages"] = [AIMessage(content="", tool_calls=tool_calls)]

        result = tool_node(state)
        assert len(result["messages"]) == 1
        assert json.loads(result["messages"][0].content) == []


class TestProcessResultsNode:
    def test_correctly_extracts_articles_from_tool_messages(
        self, state_with_tool_messages
    ):
        result = process_results_node(state_with_tool_messages)
        assert len(result["raw_articles"]) == 3
        assert result["raw_articles"][0]["url"] == "http://a.com"

    def test_handles_states_with_no_tool_messages_gracefully(self, empty_state):
        result = process_results_node(empty_state)
        assert result["raw_articles"] == []
        assert result["messages"][0].content == "Found 0 articles."

    def test_correctly_identifies_and_removes_duplicate_articles(self, empty_state):
        duplicate_results = [
            {"url": "http://a.com", "title": "A"},
            {"url": "http://b.com", "title": "B"},
            {"url": "http://a.com", "title": "A Duplicate"},
        ]
        messages = [
            ToolMessage(content=json.dumps(duplicate_results), tool_call_id="call_1")
        ]
        state = empty_state
        state["messages"] = messages

        result = process_results_node(state)
        assert len(result["raw_articles"]) == 2
        assert result["raw_articles"][0]["title"] == "A"
        assert result["raw_articles"][1]["title"] == "B"

    def test_skips_tool_messages_with_invalid_json(self, empty_state):
        messages = [ToolMessage(content="not-a-valid-json", tool_call_id="call_1")]
        state = empty_state
        state["messages"] = messages

        result = process_results_node(state)
        assert result["raw_articles"] == []

    def test_skips_tool_messages_containing_an_error(self, empty_state):
        error_message = {"error": "Tool failed to execute"}
        messages = [
            ToolMessage(content=json.dumps(error_message), tool_call_id="call_1")
        ]
        state = empty_state
        state["messages"] = messages

        result = process_results_node(state)
        assert result["raw_articles"] == []


class TestShouldContinue:
    def test_returns_continue_when_tool_calls_are_present(self, empty_state):
        tool_calls = [
            {"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}}
        ]
        state = empty_state
        state["messages"] = [AIMessage(content="", tool_calls=tool_calls)]
        assert should_continue(state) == "continue"

    def test_returns_end_when_no_tool_calls_are_present(self, empty_state):
        state = empty_state
        state["messages"] = [AIMessage(content="No tools needed.")]
        assert should_continue(state) == "end"

    def test_returns_end_when_last_message_is_not_an_ai_message(self, empty_state):
        state = empty_state
        state["messages"] = [HumanMessage(content="A user message.")]
        assert should_continue(state) == "end"
