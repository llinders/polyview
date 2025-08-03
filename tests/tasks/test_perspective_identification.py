from unittest.mock import MagicMock, patch

import pytest

from polyview.core.state import ExtractedPerspective
from polyview.tasks.perspective_identification import (
    ExtractedPerspectives,
    perspective_identification,
)


@pytest.fixture
def sample_raw_articles():
    """Provides a list of articles as dictionaries, matching the application's state."""
    return [
        {"id": "article1", "url": "http://a.com", "content": "Content for article 1."},
        {"id": "article2", "url": "http://b.com", "content": "Content for article 2."},
    ]


@pytest.fixture
def mock_llm_response():
    """Provides a valid ExtractedPerspectives object as a mock LLM response."""
    return ExtractedPerspectives(
        perspectives=[
            ExtractedPerspective(
                perspective_summary="Test Summary",
                key_arguments=["Arg 1"],
                contextual_narrative="Test Narrative",
                source_article_summary="Test Source Summary",
                inferred_assumptions=["Test Assumption"],
                evidence_provided=["Test Evidence"],
            )
        ]
    )


@patch("polyview.tasks.perspective_identification.ChatPromptTemplate")
@patch("polyview.tasks.perspective_identification.llm")
def test_perspective_identification_success(
        mock_llm, mock_prompt_template, sample_raw_articles, mock_llm_response
):
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_prompt = MagicMock()
    mock_prompt_template.from_messages.return_value = mock_prompt
    mock_final_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_final_chain
    mock_final_chain.invoke.return_value = mock_llm_response

    state = {"raw_articles": sample_raw_articles, "topic": "test"}
    result = perspective_identification(state)

    assert "article_perspectives" in result
    assert len(result["article_perspectives"]) == 2
    assert len(result["article_perspectives"][0].perspectives) == 1
    assert mock_final_chain.invoke.call_count == 2


@patch("polyview.tasks.perspective_identification.ChatPromptTemplate")
@patch("polyview.tasks.perspective_identification.llm")
def test_perspective_identification_llm_failure(
        mock_llm, mock_prompt_template, sample_raw_articles, mock_llm_response
):
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_prompt = MagicMock()
    mock_prompt_template.from_messages.return_value = mock_prompt
    mock_final_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_final_chain
    mock_final_chain.invoke.side_effect = [Exception("LLM Error"), mock_llm_response]

    state = {"raw_articles": sample_raw_articles, "topic": "test"}
    result = perspective_identification(state)

    assert len(result["article_perspectives"]) == 1
    assert result["article_perspectives"][0].source_article_id == "article2"
