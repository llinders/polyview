from unittest.mock import MagicMock, patch

import pytest

from polyview.core.state import ConsolidatedPerspective, FinalPerspective
from polyview.tasks.perspective_synthesis import (
    FinalPerspectives,
    perspective_synthesis_node,
)


@pytest.fixture
def sample_consolidated_perspectives():
    return [
        ConsolidatedPerspective(
            perspective_name="A",
            aggregated_arguments=[],
            aggregated_narratives=[],
            supporting_evidence=[],
            preliminary_synthesis="",
        )
    ]


@pytest.fixture
def mock_llm_response():
    return FinalPerspectives(
        final_perspectives=[
            FinalPerspective(
                perspective_name="A",
                narrative="",
                core_arguments=[],
                common_assumptions=[],
                strengths=[],
                weaknesses=[],
            )
        ]
    )


@patch("polyview.tasks.perspective_synthesis.ChatPromptTemplate")
@patch("polyview.tasks.perspective_synthesis.llm")
def test_perspective_synthesis_success(
        mock_llm, mock_prompt_template, sample_consolidated_perspectives, mock_llm_response
):
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_prompt = MagicMock()
    mock_prompt_template.from_messages.return_value = mock_prompt
    mock_final_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_final_chain
    mock_final_chain.invoke.return_value = mock_llm_response

    state = {"consolidated_perspectives": sample_consolidated_perspectives}
    result = perspective_synthesis_node(state)

    assert len(result["final_perspectives"]) == 1


@patch("polyview.tasks.perspective_synthesis.ChatPromptTemplate")
@patch("polyview.tasks.perspective_synthesis.llm")
def test_perspective_synthesis_llm_failure(
        mock_llm, mock_prompt_template, sample_consolidated_perspectives
):
    mock_structured_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_prompt = MagicMock()
    mock_prompt_template.from_messages.return_value = mock_prompt
    mock_final_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_final_chain
    mock_final_chain.invoke.side_effect = Exception("LLM Error")

    state = {"consolidated_perspectives": sample_consolidated_perspectives}
    result = perspective_synthesis_node(state)

    assert len(result["final_perspectives"]) == 0
