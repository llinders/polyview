import pytest
from unittest.mock import MagicMock, patch

from polyview.agents.search_agent import run_search_agent


@pytest.mark.integration
@patch("polyview.agents.search_agent.search_agent_graph")
def test_search_node_returns_expected_command(mock_agent_graph):
    # Arrange: fake state and mock agent response
    fake_state = {"messages": [{"content": "What is the capital of France?"}]}

    mock_agent_graph.invoke.return_value = {
        "raw_articles": [
            {"id": "test_id", "url": "http://example.com", "content": "Test content"}
        ],
        "messages": [
            MagicMock(content="The capital of France is Paris.")
        ]
    }

    # Act
    result = run_search_agent(fake_state)

    # Assert
    assert "raw_articles" in result
    assert "messages" in result
    assert result["messages"][0].content == "The capital of France is Paris."