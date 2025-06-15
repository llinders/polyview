from unittest.mock import MagicMock, patch
from langgraph.types import Command
from src.agents.search_agent import search_node


@patch("agents.search_agent.search_agent")
def test_search_node_returns_expected_command(mock_agent):
    # Arrange: fake state and mock agent response
    fake_state = {"messages": [{"content": "What is the capital of France?"}]}

    mock_agent.invoke.return_value = {
        "messages": [
            MagicMock(content="The capital of France is Paris.")
        ]
    }

    # Act
    command = search_node(fake_state)

    # Assert
    assert isinstance(command, Command)
    assert "messages" in command.update
    assert command.update["messages"][0].content == "The capital of France is Paris."
    assert command.update["messages"][0].name == "search"
    assert command.goto == "__end__"