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
    _flatten_perspectives,
    _format_perspectives_for_prompt,
    _process_clustering_result,
)


@pytest.fixture
def sample_extracted_perspectives_data() -> list[ArticlePerspectives]:
    return [
        ArticlePerspectives(
            source_article_id="id1",
            perspectives=[
                ExtractedPerspective(
                    perspective_summary="Summary 1A",
                    key_arguments=["Arg 1A.1", "Arg 1A.2"],
                    contextual_narrative="Narrative 1A",
                    source_article_summary="Source Summary 1A",
                    inferred_assumptions=["Assumption 1A"],
                    evidence_provided=["Evidence 1A"],
                ),
                ExtractedPerspective(
                    perspective_summary="Summary 1B",
                    key_arguments=["Arg 1B.1", "Arg 1B.2"],
                    contextual_narrative="Narrative 1B",
                    source_article_summary="Source Summary 1B",
                    inferred_assumptions=["Assumption 1B"],
                    evidence_provided=["Evidence 1B"],
                ),
            ],
        ),
        ArticlePerspectives(
            source_article_id="id2",
            perspectives=[
                ExtractedPerspective(
                    perspective_summary="Summary 2A",
                    key_arguments=["Arg 2A.1", "Arg 2A.2", "Arg 1A.1"],
                    contextual_narrative="Narrative 2A",
                    source_article_summary="Source Summary 2A",
                    inferred_assumptions=["Assumption 2A"],
                    evidence_provided=["Evidence 2A"],
                )
            ],
        ),
    ]


@pytest.fixture
def sample_flattened_perspectives(
    sample_extracted_perspectives_data,
) -> list[ExtractedPerspective]:
    return _flatten_perspectives(sample_extracted_perspectives_data)


@pytest.fixture
def sample_clustering_result() -> ClusteringResult:
    return ClusteringResult(
        clusters=[
            PerspectiveCluster(
                cluster_name="Cluster A",
                perspective_indices=[0, 2],  # Corresponds to Summary 1A and Summary 2A
            ),
            PerspectiveCluster(
                cluster_name="Cluster B",
                perspective_indices=[1],  # Corresponds to Summary 1B
            ),
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
    @patch(
        "polyview.tasks.perspective_clustering._create_synthesis_prompt",
        return_value="Synthesized Narrative",
    )
    def test_basic_consolidation(
        self, mock_synthesis, sample_clustering_result, sample_flattened_perspectives
    ):
        consolidated_list = _process_clustering_result(
            sample_clustering_result, sample_flattened_perspectives, [], iteration=1
        )

        assert isinstance(consolidated_list, list)
        assert len(consolidated_list) == 2

        cluster_a_found = next(
            (cp for cp in consolidated_list if cp.perspective_name == "Cluster A"), None
        )
        cluster_b_found = next(
            (cp for cp in consolidated_list if cp.perspective_name == "Cluster B"), None
        )

        assert cluster_a_found is not None
        assert cluster_b_found is not None

        assert set(cluster_a_found.aggregated_arguments) == {
            "Arg 1A.1",
            "Arg 1A.2",
            "Arg 2A.1",
            "Arg 2A.2",
        }
        assert set(cluster_b_found.aggregated_arguments) == {"Arg 1B.1", "Arg 1B.2"}
        assert cluster_a_found.preliminary_synthesis == "Synthesized Narrative"

    @patch(
        "polyview.tasks.perspective_clustering._create_synthesis_prompt",
        return_value="Synthesized Narrative",
    )
    def test_empty_clusters_input(self, mock_synthesis):
        empty_result = ClusteringResult(clusters=[])
        assert _process_clustering_result(empty_result, [], [], iteration=1) == []

    @patch(
        "polyview.tasks.perspective_clustering._create_synthesis_prompt",
        return_value="Synthesized Narrative",
    )
    def test_invalid_perspective_index_handling(
        self, mock_synthesis, sample_clustering_result, sample_flattened_perspectives
    ):
        invalid_cluster = PerspectiveCluster(
            cluster_name="Invalid Cluster", perspective_indices=[999]
        )
        test_clustering_result = ClusteringResult(
            clusters=sample_clustering_result.clusters + [invalid_cluster]
        )

        consolidated_list = _process_clustering_result(
            test_clustering_result, sample_flattened_perspectives, [], iteration=1
        )

        invalid_cluster_found = next(
            (
                cp
                for cp in consolidated_list
                if cp.perspective_name == "Invalid Cluster"
            ),
            None,
        )

        assert invalid_cluster_found is not None
        assert invalid_cluster_found.aggregated_arguments == []

    @patch(
        "polyview.tasks.perspective_clustering._create_synthesis_prompt",
        return_value="Synthesized Narrative",
    )
    def test_duplicate_arguments_are_unique(
        self, mock_synthesis, sample_flattened_perspectives
    ):
        clustering_result = ClusteringResult(
            clusters=[
                PerspectiveCluster(
                    cluster_name="Duplicate Arg Cluster",
                    perspective_indices=[0, 2],  # Summary 1A and 2A share "Arg 1A.1"
                )
            ]
        )

        consolidated_list = _process_clustering_result(
            clustering_result, sample_flattened_perspectives, [], iteration=1
        )

        assert len(consolidated_list) == 1
        cluster = consolidated_list[0]

        assert cluster.aggregated_arguments.count("Arg 1A.1") == 1
        assert len(cluster.aggregated_arguments) == 4

    @patch(
        "polyview.tasks.perspective_clustering._create_synthesis_prompt",
        return_value="Synthesized Narrative",
    )
    def test_with_existing_perspectives(
        self, mock_synthesis, sample_clustering_result, sample_flattened_perspectives
    ):
        existing_perspectives = [
            FinalPerspective(
                perspective_name="Cluster A",
                narrative="Existing Narrative",
                core_arguments=["Existing Arg"],
                common_assumptions=[],
                strengths=["Existing Strength"],
                weaknesses=[],
                supporting_evidence=["Existing Evidence"],
            )
        ]

        consolidated_list = _process_clustering_result(
            sample_clustering_result,
            sample_flattened_perspectives,
            existing_perspectives,
            iteration=1,
        )

        cluster_a_found = next(
            (cp for cp in consolidated_list if cp.perspective_name == "Cluster A"), None
        )

        assert cluster_a_found is not None
        assert "Existing Arg" in cluster_a_found.aggregated_arguments
        assert "Existing Narrative" in cluster_a_found.aggregated_narratives
