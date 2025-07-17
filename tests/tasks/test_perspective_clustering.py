import pytest
from typing import List, Dict

from polyview.core.state import ExtractedPerspective, ConsolidatedPerspective
from polyview.tasks.perspective_clustering import (
    _flatten_perspectives,
    _format_perspectives_for_prompt,
    _process_clustering_result,
    ClusteringResult,
    PerspectiveCluster
)

# Sample data for testing
@pytest.fixture
def sample_extracted_perspectives_data() -> Dict[str, List[Dict]]:
    return {
        "article_1": [
            {
                "perspective_summary": "Summary 1A",
                "key_arguments": ["Arg 1A.1", "Arg 1A.2"]
            },
            {
                "perspective_summary": "Summary 1B",
                "key_arguments": ["Arg 1B.1", "Arg 1B.2"]
            },
        ],
        "article_2": [
            {
                "perspective_summary": "Summary 2A",
                "key_arguments": ["Arg 2A.1", "Arg 2A.2", "Arg 1A.1"]
            }
        ]
    }

@pytest.fixture
def sample_flattened_perspectives(sample_extracted_perspectives_data) -> List[ExtractedPerspective]:
    return _flatten_perspectives(sample_extracted_perspectives_data)

@pytest.fixture
def sample_clustering_result() -> ClusteringResult:
    return ClusteringResult(
        clusters=[
            PerspectiveCluster(
                cluster_name="Cluster A",
                perspective_indices=[0, 2] # Corresponds to Summary 1A and Summary 2A
            ),
            PerspectiveCluster(
                cluster_name="Cluster B",
                perspective_indices=[1] # Corresponds to Summary 1B
            )
        ]
    )


# Test for _flatten_perspectives
def test_flatten_perspectives_empty():
    assert _flatten_perspectives({}) == []

def test_flatten_perspectives_single_article(sample_extracted_perspectives_data):
    flattened = _flatten_perspectives({"article_1": sample_extracted_perspectives_data["article_1"]})
    assert len(flattened) == 2
    assert all(isinstance(p, ExtractedPerspective) for p in flattened)
    assert flattened[0].perspective_summary == "Summary 1A"
    assert flattened[1].perspective_summary == "Summary 1B"

def test_flatten_perspectives_multiple_articles(sample_extracted_perspectives_data):
    flattened = _flatten_perspectives(sample_extracted_perspectives_data)
    assert len(flattened) == 3
    assert all(isinstance(p, ExtractedPerspective) for p in flattened)
    assert flattened[0].perspective_summary == "Summary 1A"
    assert flattened[1].perspective_summary == "Summary 1B"
    assert flattened[2].perspective_summary == "Summary 2A"


# Test for _format_perspectives_for_prompt
def test_format_perspectives_for_prompt_empty():
    assert _format_perspectives_for_prompt([]) == []

def test_format_perspectives_for_prompt_with_data(sample_flattened_perspectives):
    formatted = _format_perspectives_for_prompt(sample_flattened_perspectives)
    assert len(formatted) == 3
    assert formatted[0] == {"index": 0, "summary": "Summary 1A"}
    assert formatted[1] == {"index": 1, "summary": "Summary 1B"}
    assert formatted[2] == {"index": 2, "summary": "Summary 2A"}


# Test for _process_clustering_result
def test_process_clustering_result(sample_clustering_result, sample_flattened_perspectives):
    consolidated = _process_clustering_result(sample_clustering_result, sample_flattened_perspectives)
    
    assert "Cluster A" in consolidated
    assert "Cluster B" in consolidated
    assert isinstance(consolidated["Cluster A"], ConsolidatedPerspective)
    assert isinstance(consolidated["Cluster B"], ConsolidatedPerspective)

    # Check arguments for Cluster A (Summary 1A and Summary 2A)
    # Arg 1A.1 should appear once, Arg 1A.2 once, Arg 2A.1 once, Arg 2A.2 once
    assert sorted(consolidated["Cluster A"].arguments) == sorted(["Arg 1A.1", "Arg 1A.2", "Arg 2A.1", "Arg 2A.2"])

    # Check arguments for Cluster B (Summary 1B)
    assert consolidated["Cluster B"].arguments == ["Arg 1B.1", "Arg 1B.2"]

def test_process_clustering_result_empty_clusters():
    empty_result = ClusteringResult(clusters=[])
    assert _process_clustering_result(empty_result, []) == {}

def test_process_clustering_result_invalid_index(sample_clustering_result, sample_flattened_perspectives):
    # Create a result with an invalid index
    invalid_cluster = PerspectiveCluster(
        cluster_name="Invalid Cluster",
        perspective_indices=[999] # Index out of bounds
    )
    sample_clustering_result.clusters.append(invalid_cluster)

    consolidated = _process_clustering_result(sample_clustering_result, sample_flattened_perspectives)
    assert "Invalid Cluster" in consolidated
    assert consolidated["Invalid Cluster"].arguments == [] # Should be empty as index is invalid
