from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage
import pytest

if TYPE_CHECKING:
    from polyview.core.state import State

from polyview.tasks.topic_refinement import topic_refinement_agent


@pytest.mark.integration
def test_refine_clear_topic():
    """Tests that a clear user request is refined into a research topic."""
    initial_state: State = {
        "messages": [
            HumanMessage(
                content="Tell me about the pros and cons of using nuclear energy to fight climate change."
            )
        ]
    }
    result = topic_refinement_agent(initial_state)
    assert result["topic"] != "clarify"
    assert isinstance(result["topic"], str)
    assert "nuclear energy" in result["topic"].lower()
    assert "climate change" in result["topic"].lower()


@pytest.mark.integration
def test_clarify_greeting():
    """Tests that a simple greeting results in a request for clarification."""
    initial_state: State = {"messages": [HumanMessage(content="Hello there!")]}
    result = topic_refinement_agent(initial_state)
    assert result["topic"] == "clarify"


@pytest.mark.integration
def test_clarify_ambiguous_request():
    """Tests that a vague or nonsensical request results in clarification."""
    initial_state: State = {"messages": [HumanMessage(content="How are you?")]}
    result = topic_refinement_agent(initial_state)
    assert result["topic"] == "clarify"


@pytest.mark.integration
def test_refine_complex_but_clear_topic():
    """Tests a more complex but still clear topic."""
    initial_state: State = {
        "messages": [
            HumanMessage(
                content="I'm interested in the geopolitical implications of China's investment in African infrastructure."
            )
        ]
    }
    result = topic_refinement_agent(initial_state)
    assert result["topic"] != "clarify"
    assert isinstance(result["topic"], str)
    assert "china" or "chinese" in result["topic"].lower()
    assert "africa" or "african" in result["topic"].lower()
    assert "geopolitical" in result["topic"].lower()
