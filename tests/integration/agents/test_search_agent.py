from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage
import pytest

from polyview.agents.search_agent import run_search_agent
from polyview.core.state import State


@pytest.fixture
def initial_state() -> State:
    """Provides a standard initial state for integration tests."""
    return {
        "messages": [HumanMessage(content="Research climate change.")],
        "topic": "climate change",
        "raw_articles": [],
        "article_perspectives": [],
        "consolidated_perspectives": [],
        "final_perspectives": [],
        "summary": "",
        "iteration": 0,
        "missing_perspectives": [],
    }


@pytest.mark.integration
@patch("polyview.agents.search_agent.search_agent_graph")
def test_run_search_agent_end_to_end_flow(mock_agent_graph, initial_state):
    """Tests the full end-to-end flow of the search agent graph."""
    # Arrange: Mock the graph's invoke method to simulate a full run
    mock_agent_graph.invoke.return_value = {
        "raw_articles": [
            {"id": "test_id", "url": "http://example.com", "content": "Test content"}
        ],
        "messages": [AIMessage(content="Search complete.")],
    }

    # Act
    result = run_search_agent(initial_state)

    # Assert
    assert "raw_articles" in result
    assert len(result["raw_articles"]) == 1
    assert result["raw_articles"][0]["url"] == "http://example.com"
    assert "messages" in result
    assert result["messages"][0].content == "Search complete."
    mock_agent_graph.invoke.assert_called_once()


@pytest.mark.integration
@patch("polyview.agents.search_agent.search_agent_graph")
def test_run_search_agent_immediate_end(mock_agent_graph, initial_state):
    """Tests that the graph correctly handles an immediate end condition."""
    # Arrange: Mock the graph to return a message without tool calls
    mock_agent_graph.invoke.return_value = {
        "raw_articles": [],
        "messages": [AIMessage(content="No search needed.")],
    }

    # Act
    result = run_search_agent(initial_state)

    # Assert
    assert "raw_articles" in result
    assert len(result["raw_articles"]) == 0
    assert "messages" in result
    assert result["messages"][0].content == "No search needed."
    mock_agent_graph.invoke.assert_called_once()
