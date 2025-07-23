from typing import List

import pytest

from polyview.core.state import ExtractedPerspective, ConsolidatedPerspective, ArticlePerspectives
from polyview.tasks.perspective_clustering import (
    _flatten_perspectives,
    _format_perspectives_for_prompt,
    _process_clustering_result,
    ClusteringResult,
    PerspectiveCluster
)


@pytest.fixture
def sample_extracted_perspectives_data() -> List[ArticlePerspectives]:
    return [
        ArticlePerspectives(
            source_article_id='id1',
            perspectives=[
                ExtractedPerspective(
                    perspective_summary="Summary 1A",
                    key_arguments=["Arg 1A.1", "Arg 1A.2"]
                ),
                ExtractedPerspective(
                    perspective_summary="Summary 1B",
                    key_arguments=["Arg 1B.1", "Arg 1B.2"]
                ),
            ]
        ),
        ArticlePerspectives(
            source_article_id='id2',
            perspectives=[
                ExtractedPerspective(
                    perspective_summary="Summary 2A",
                    key_arguments=["Arg 2A.1", "Arg 2A.2", "Arg 1A.1"]
                )
            ]
        )
    ]

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


class TestFlattenPerspectives:
    def test_empty_list(self):
        assert _flatten_perspectives([]) == []

    def test_single_article_input(self, sample_extracted_perspectives_data):
        flattened = _flatten_perspectives([sample_extracted_perspectives_data[0]])
        assert len(flattened) == 2
        assert all(isinstance(p, ExtractedPerspective) for p in flattened)
        assert flattened[0].perspective_summary == "Summary 1A"
        assert flattened[1].perspective_summary == "Summary 1B"

    def test_multiple_articles_input(self, sample_extracted_perspectives_data):
        flattened = _flatten_perspectives(sample_extracted_perspectives_data)
        assert len(flattened) == 3
        assert all(isinstance(p, ExtractedPerspective) for p in flattened)
        assert flattened[0].perspective_summary == "Summary 1A"
        assert flattened[1].perspective_summary == "Summary 1B"
        assert flattened[2].perspective_summary == "Summary 2A"


class TestFormatPerspectivesForPrompt:
    def test_empty_list(self):
        assert _format_perspectives_for_prompt([]) == []

    def test_with_data(self, sample_flattened_perspectives):
        formatted = _format_perspectives_for_prompt(sample_flattened_perspectives)
        assert len(formatted) == 3
        assert formatted[0] == {"index": 0, "summary": "Summary 1A"}
        assert formatted[1] == {"index": 1, "summary": "Summary 1B"}
        assert formatted[2] == {"index": 2, "summary": "Summary 2A"}


class TestProcessClusteringResult:
    def test_basic_consolidation(self, sample_clustering_result, sample_flattened_perspectives):
        consolidated_list = _process_clustering_result(sample_clustering_result, sample_flattened_perspectives)

        assert isinstance(consolidated_list, list)
        assert len(consolidated_list) == 2

        cluster_a_found = None
        cluster_b_found = None
        for cp in consolidated_list:
            if cp.perspective_name == "Cluster A":
                cluster_a_found = cp
            elif cp.perspective_name == "Cluster B":
                cluster_b_found = cp

        assert cluster_a_found is not None
        assert cluster_b_found is not None

        assert isinstance(cluster_a_found, ConsolidatedPerspective)
        assert isinstance(cluster_b_found, ConsolidatedPerspective)

        # Check arguments for Cluster A
        assert set(cluster_a_found.arguments) == {"Arg 1A.1", "Arg 1A.2", "Arg 2A.1", "Arg 2A.2"}

        # Check arguments for Cluster B
        assert set(cluster_b_found.arguments) == {"Arg 1B.1", "Arg 1B.2"}

    def test_empty_clusters_input(self):
        empty_result = ClusteringResult(clusters=[])
        assert _process_clustering_result(empty_result, []) == []

    def test_invalid_perspective_index_handling(self, sample_clustering_result, sample_flattened_perspectives):
        # Create a result with an invalid index
        invalid_cluster = PerspectiveCluster(
            cluster_name="Invalid Cluster",
            perspective_indices=[999]  # Index out of bounds
        )
        test_clustering_result = ClusteringResult(clusters=sample_clustering_result.clusters + [invalid_cluster])

        consolidated_list = _process_clustering_result(test_clustering_result, sample_flattened_perspectives)

        invalid_cluster_found = None
        for cp in consolidated_list:
            if cp.perspective_name == "Invalid Cluster":
                invalid_cluster_found = cp
                break

        assert invalid_cluster_found is not None
        assert invalid_cluster_found.arguments == []  # Should be empty as index is invalid

    def test_duplicate_arguments_are_unique(self, sample_flattened_perspectives):
        clustering_result = ClusteringResult(
            clusters=[
                PerspectiveCluster(
                    cluster_name="Duplicate Arg Cluster",
                    perspective_indices=[0, 2]  # Summary 1A and 2A share "Arg 1A.1"
                )
            ]
        )

        consolidated_list = _process_clustering_result(clustering_result, sample_flattened_perspectives)
        
        assert len(consolidated_list) == 1
        cluster = consolidated_list[0]

        # Check that "Arg 1A.1" appears only once
        assert cluster.arguments.count("Arg 1A.1") == 1
        assert len(cluster.arguments) == 4  # Arg 1A.1, Arg 1A.2, Arg 2A.1, Arg 2A.2
