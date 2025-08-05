from unittest.mock import patch

import pytest

from polyview.core.state import (
    ArticlePerspectives,
    ExtractedPerspective,
    FinalPerspective,
)
from polyview.tasks.perspective_clustering import (
    ClusteringResult,
    PerspectiveCluster,
    perspective_clustering_node,
)


@pytest.fixture
def initial_perspectives_fixture():
    """Provides the initial set of perspectives for the tests."""
    return [
        ArticlePerspectives(
            source_article_id="article1",
            perspectives=[
                ExtractedPerspective(
                    perspective_summary="Remote work boosts productivity.",
                    key_arguments=["Increased autonomy", "Reduced commute"],
                    contextual_narrative="...",
                    source_article_summary="...",
                    inferred_assumptions=["..."],
                    evidence_provided=["..."],
                ),
                ExtractedPerspective(
                    perspective_summary="Remote work harms culture.",
                    key_arguments=["Less collaboration", "Harder onboarding"],
                    contextual_narrative="...",
                    source_article_summary="...",
                    inferred_assumptions=["..."],
                    evidence_provided=["..."],
                ),
            ],
        ),
    ]


@pytest.fixture
def new_perspectives_fixture():
    """Provides the new perspectives for the iterative clustering test."""
    return [
        ArticlePerspectives(
            source_article_id="article2",
            perspectives=[
                ExtractedPerspective(
                    perspective_summary="Hybrid models are optimal.",
                    key_arguments=["Flexibility", "Scheduled collaboration"],
                    contextual_narrative="...",
                    source_article_summary="...",
                    inferred_assumptions=["..."],
                    evidence_provided=["..."],
                ),
                ExtractedPerspective(
                    perspective_summary="Remote work hurts career growth.",
                    key_arguments=["Less visibility", "Reduced mentorship"],
                    contextual_narrative="...",
                    source_article_summary="...",
                    inferred_assumptions=["..."],
                    evidence_provided=["..."],
                ),
            ],
        ),
    ]


@pytest.mark.integration
@patch(
    "polyview.tasks.perspective_clustering._create_synthesis_prompt",
    return_value="Synthesized Narrative",
)
@patch("langchain_core.runnables.base.RunnableSequence.invoke")
def test_perspective_clustering_iterative(
    mock_chain_invoke,
    mock_synthesis,
    initial_perspectives_fixture,
    new_perspectives_fixture,
):
    # === Phase 1: Initial Clustering ===

    # Arrange: Mock the LLM for the first run
    mock_chain_invoke.return_value = ClusteringResult(
        clusters=[
            PerspectiveCluster(cluster_name="Pro-Remote", perspective_indices=[0]),
            PerspectiveCluster(cluster_name="Anti-Remote", perspective_indices=[1]),
        ]
    )
    initial_state = {
        "article_perspectives": initial_perspectives_fixture,
        "final_perspectives": [],
        "iteration": 1,
    }

    # Act: Run the clustering node for the first time
    first_run_state = perspective_clustering_node(initial_state)

    # Assert: Check if the initial clusters are created correctly
    assert len(first_run_state["consolidated_perspectives"]) == 2
    pro_remote_cluster = next(
        p
        for p in first_run_state["consolidated_perspectives"]
        if p.perspective_name == "Pro-Remote"
    )
    assert "Increased autonomy" in pro_remote_cluster.aggregated_arguments

    # === Phase 2: Iterative Clustering ===

    # Arrange: Mock the LLM for the second run to merge and add clusters
    mock_chain_invoke.return_value = ClusteringResult(
        clusters=[
            # Note: The indices here are for the *new* perspectives list
            PerspectiveCluster(
                cluster_name="Anti-Remote", perspective_indices=[1]
            ),  # Merges with existing
            PerspectiveCluster(
                cluster_name="Hybrid-Model", perspective_indices=[0]
            ),  # Creates a new one
        ]
    )

    # Arrange: Convert consolidated perspectives to final perspectives for the next run
    # This simulates the state after a full synthesis step would have run on the consolidated perspectives.
    final_perspectives_for_next_run = [
        FinalPerspective(
            perspective_name=p.perspective_name,
            narrative=p.preliminary_synthesis,
            core_arguments=p.aggregated_arguments,
            supporting_evidence=p.supporting_evidence,
            common_assumptions=[],  # Not the focus of this test
            strengths=[],  # Not the focus of this test
            weaknesses=[],  # Not the focus of this test
        )
        for p in first_run_state["consolidated_perspectives"]
    ]

    iterative_state = {
        "article_perspectives": new_perspectives_fixture,
        "final_perspectives": final_perspectives_for_next_run,
        "iteration": 2,
    }

    # Act: Run the clustering node for the second time
    second_run_state = perspective_clustering_node(iterative_state)

    # Assert: Check the results of the iterative clustering
    assert len(second_run_state["consolidated_perspectives"]) == 2

    anti_remote_iterative = next(
        p
        for p in second_run_state["consolidated_perspectives"]
        if p.perspective_name == "Anti-Remote"
    )
    hybrid_iterative = next(
        p
        for p in second_run_state["consolidated_perspectives"]
        if p.perspective_name == "Hybrid-Model"
    )

    # Check that new arguments were added to the existing cluster
    assert "Less visibility" in anti_remote_iterative.aggregated_arguments
    # Check that old arguments are still present
    assert "Less collaboration" in anti_remote_iterative.aggregated_arguments
    # Check that the new cluster was created correctly
    assert "Flexibility" in hybrid_iterative.aggregated_arguments

    # Assert: Verify that our mocks were called as expected.
    assert mock_chain_invoke.call_count == 2
    assert mock_synthesis.call_count == 4
