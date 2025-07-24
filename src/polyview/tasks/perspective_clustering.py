from typing import List, Dict

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.logging import get_logger
from polyview.core.state import State, ConsolidatedPerspective, ExtractedPerspective, ArticlePerspectives

logger = get_logger(__name__)


class PerspectiveCluster(BaseModel):
    """A single cluster of similar perspectives."""
    cluster_name: str = (
        Field(
            description="A short, descriptive name for the cluster (e.g., 'Scientific Consensus', 'Techno-Optimist', "
                        "'Skeptical/Contrarian', 'Justice-Oriented', 'Economic Impact Concerns', 'Geopolitical Risks', "
                        "'Conservative', 'Liberal', etc. The name should immediately convey the essence of the perspective."
        ))
    perspective_indices: List[int] = Field(
        description="The list of indices corresponding to the original perspectives that belong to this cluster."
    )


class ClusteringResult(BaseModel):
    """The result of clustering all perspectives."""
    clusters: List[PerspectiveCluster]


def _flatten_perspectives(article_perspectives_list: List[ArticlePerspectives]) -> List[ExtractedPerspective]:
    """
    Flattens a list of ArticlePerspectives into a single list of ExtractedPerspective objects.
    This function handles cases where the input list contains dictionaries instead of Pydantic objects.
    """
    all_perspectives: List[ExtractedPerspective] = []
    # The data from the state can be a list of dicts, so we parse them into ArticlePerspectives objects.
    for item in article_perspectives_list:
        if isinstance(item, dict):
            article_p = ArticlePerspectives.model_validate(item)
        else:
            article_p = item  # Assume it's already an ArticlePerspectives object
        all_perspectives.extend(article_p.perspectives)
    return all_perspectives


def _format_perspectives_for_prompt(all_perspectives: List[ExtractedPerspective]) -> List[Dict]:
    """Formats perspectives for the LLM prompt, including their original index and summary."""
    return [
        {"index": i, "summary": p.perspective_summary}
        for i, p in enumerate(all_perspectives)
    ]


def _process_clustering_result(result: ClusteringResult, all_perspectives: List[ExtractedPerspective]) -> List[
    ConsolidatedPerspective]:
    """Processes the clustering result to consolidate arguments for each cluster."""
    consolidated_perspectives: List[ConsolidatedPerspective] = []
    for cluster in result.clusters:
        cluster_name = cluster.cluster_name
        all_arguments = []
        for index in cluster.perspective_indices:
            if 0 <= index < len(all_perspectives):
                all_arguments.extend(all_perspectives[index].key_arguments)

        unique_arguments = list(dict.fromkeys(all_arguments))
        consolidated_perspectives.append(
            ConsolidatedPerspective(perspective_name=cluster_name, arguments=unique_arguments))
        logger.info(f"Created cluster '{cluster_name}' with {len(unique_arguments)} unique arguments.")
    return consolidated_perspectives


def perspective_clustering_node(state: State) -> dict:
    """
    Analyzes and clusters semantically similar perspectives into a consolidated view.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an advanced analytical AI specializing in synthesizing diverse viewpoints into coherent, distinct perspectives. Your primary goal is to group a given list of individual perspective summaries into semantically similar clusters. Each cluster should represent a unique, meaningful, and well-defined core argument or viewpoint on the topic.

Crucial Guidelines for Clustering:
1.  **Holistic View:** Aim to create clusters that collectively offer a comprehensive and balanced understanding of the topic, covering the main schools of thought or arguments.
2.  **Distinctness:** Each cluster must represent a clearly distinguishable perspective. Avoid creating clusters that are too broad, vague, or overlap significantly. Conversely, do not scatter closely related perspectives into too many separate, minor clusters.
3.  **Core Argument Focus:** Identify perspectives that share the *same fundamental argument or central claim*, even if expressed with different wording or nuances.
4.  **Cluster Naming:** For each identified cluster, provide a concise, descriptive, and neutral name that accurately captures its core idea. The name should immediately convey the essence of the perspective.
5.  **Assignment:** Accurately assign the original indices of all perspectives that belong to each cluster.

"""
            ),
            (
                "human",
                """Please cluster the following perspectives:
```json
{perspectives}
```"""
            ),
        ]
    )

    structured_llm = llm.with_structured_output(ClusteringResult)
    chain = prompt | structured_llm

    article_perspectives_list = state.get("article_perspectives")
    logger.debug(f"extracted_perspectives: {article_perspectives_list}")

    if not article_perspectives_list:
        logger.info("No perspectives found to consolidate. Skipping clustering node..")
        return {"consolidated_perspectives": []}

    all_perspectives = _flatten_perspectives(article_perspectives_list)
    logger.debug(f"all_perspectives: {all_perspectives}")

    if not all_perspectives:
        logger.info("No perspectives found to consolidate. Skipping clustering node..")
        return {"consolidated_perspectives": []}

    perspectives_for_prompt = _format_perspectives_for_prompt(all_perspectives)

    logger.info(f"--- Clustering {len(all_perspectives)} perspectives ---")
    result = chain.invoke({"perspectives": perspectives_for_prompt})
    consolidated_perspectives = _process_clustering_result(result, all_perspectives)

    return {"consolidated_perspectives": consolidated_perspectives}
