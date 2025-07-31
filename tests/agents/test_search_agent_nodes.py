from unittest.mock import patch, MagicMock

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from polyview.agents.search_agent import formatter_node, SearchAnalysis, Article
from polyview.core.state import State


@pytest.fixture
def initial_state():
    return State(
        messages=[HumanMessage(content="Research climate change.")],
        topic="climate change",
        raw_articles=[], article_perspectives=[], consolidated_perspectives=[],
        final_perspectives=[], summary="", iteration=0, missing_perspectives=[]
    )


@patch('polyview.agents.search_agent.ChatPromptTemplate')
@patch('polyview.agents.search_agent.llm')
def test_formatter_node_structures_output(mock_llm, mock_prompt_template, initial_state):
    """Tests that the formatter_node correctly parses the LLM output."""
    state_with_summary = initial_state.copy()
    state_with_summary["messages"].append(AIMessage(content="Final summary of findings."))

    mock_structured_result = SearchAnalysis(
        summary="Structured summary.",
        articles=[
            Article(url="http://a.com", title="A", content="..."),
            Article(url="http://b.com", title="B", content="...")
        ]
    )

    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_prompt = MagicMock()
    mock_prompt_template.from_messages.return_value = mock_prompt
    mock_final_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_final_chain
    mock_final_chain.invoke.return_value = mock_structured_result

    result = formatter_node(state_with_summary)

    assert "raw_articles" in result
    assert len(result["raw_articles"]) == 2
    assert result["raw_articles"][0]["url"] == "http://a.com"
    assert "Search summary: Structured summary." in result["messages"][0].content
