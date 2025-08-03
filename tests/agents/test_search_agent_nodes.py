import json
from unittest.mock import patch

import pytest
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from polyview.agents.search_agent import process_results_node, tool_node
from polyview.core.state import State


@pytest.fixture
def empty_state() -> State:
    """Provides a fresh, empty state for testing initial conditions."""
    return State(
        messages=[], topic="", raw_articles=[], article_perspectives=[],
        consolidated_perspectives=[], final_perspectives=[], summary="",
        iteration=0, missing_perspectives=[]
    )


@pytest.fixture
def state_with_tool_messages() -> State:
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

    return State(
        messages=messages,
        topic="climate change",
        raw_articles=[], article_perspectives=[], consolidated_perspectives=[],
        final_perspectives=[], summary="", iteration=0, missing_perspectives=[]
    )


class TestToolNode:
    @patch('polyview.agents.search_agent.search_tool')
    def test_returns_empty_list_when_no_tool_calls_are_present(self, mock_search_tool, empty_state):
        state = empty_state
        state["messages"] = [AIMessage(content="No tools needed.")]
        result = tool_node(state)
        assert result["messages"] == []
        mock_search_tool.invoke.assert_not_called()

    @patch('polyview.agents.search_agent.search_tool')
    def test_correctly_handles_multiple_tool_calls(self, mock_search_tool):
        mock_search_tool.invoke.side_effect = [
            {"results": [{"url": "http://a.com", "score": 0.9}]},
            {"results": [{"url": "http://b.com", "score": 0.8}]},
        ]
        tool_calls = [
            {"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}},
            {"id": "call_2", "name": "tavily_search", "args": {"query": "q2"}},
        ]
        state = State(messages=[AIMessage(content="", tool_calls=tool_calls)])

        result = tool_node(state)
        assert len(result["messages"]) == 2
        assert json.loads(result["messages"][0].content)[0]["url"] == "http://a.com"
        assert json.loads(result["messages"][1].content)[0]["url"] == "http://b.com"

    @patch('polyview.agents.search_agent.search_tool')
    def test_gracefully_handles_tool_failure(self, mock_search_tool):
        mock_search_tool.invoke.side_effect = Exception("API limit reached")
        tool_calls = [{"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}}]
        state = State(messages=[AIMessage(content="", tool_calls=tool_calls)])

        result = tool_node(state)
        assert len(result["messages"]) == 1
        error_content = json.loads(result["messages"][0].content)
        assert "error" in error_content
        assert error_content["error"] == "API limit reached"

    @patch('polyview.agents.search_agent.search_tool')
    def test_handles_empty_search_results(self, mock_search_tool):
        mock_search_tool.invoke.return_value = {"results": []}
        tool_calls = [{"id": "call_1", "name": "tavily_search", "args": {"query": "q1"}}]
        state = State(messages=[AIMessage(content="", tool_calls=tool_calls)])

        result = tool_node(state)
        assert len(result["messages"]) == 1
        assert json.loads(result["messages"][0].content) == []


class TestProcessResultsNode:
    def test_correctly_extracts_articles_from_tool_messages(self, state_with_tool_messages):
        result = process_results_node(state_with_tool_messages)
        assert len(result["raw_articles"]) == 3
        assert result["raw_articles"][0]["url"] == "http://a.com"

    def test_handles_states_with_no_tool_messages_gracefully(self, empty_state):
        result = process_results_node(empty_state)
        assert result["raw_articles"] == []
        assert result["messages"][0].content == "Found 0 articles."

    def test_correctly_identifies_and_removes_duplicate_articles(self):
        duplicate_results = [
            {"url": "http://a.com", "title": "A"},
            {"url": "http://b.com", "title": "B"},
            {"url": "http://a.com", "title": "A Duplicate"},
        ]
        messages = [ToolMessage(content=json.dumps(duplicate_results), tool_call_id="call_1")]
        state = State(messages=messages)

        result = process_results_node(state)
        assert len(result["raw_articles"]) == 2
        assert result["raw_articles"][0]["title"] == "A"
        assert result["raw_articles"][1]["title"] == "B"
