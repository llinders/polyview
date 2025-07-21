from typing import List, Dict

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.state import State, ConsolidatedPerspective, ExtractedPerspective, ArticlePerspectives


class PerspectiveCluster(BaseModel):
    """A single cluster of similar perspectives."""
    cluster_name: str = Field(description="A short, descriptive name for the cluster (e.g., 'Techno-Optimist').")
    perspective_indices: List[int] = Field(description="The list of indices corresponding to the original perspectives that belong to this cluster.")

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

def _process_clustering_result(result: ClusteringResult, all_perspectives: List[ExtractedPerspective]) -> List[ConsolidatedPerspective]:
    """Processes the clustering result to consolidate arguments for each cluster."""
    consolidated_perspectives: List[ConsolidatedPerspective] = []
    for cluster in result.clusters:
        cluster_name = cluster.cluster_name
        all_arguments = []
        for index in cluster.perspective_indices:
            if 0 <= index < len(all_perspectives):
                all_arguments.extend(all_perspectives[index].key_arguments)

        unique_arguments = list(dict.fromkeys(all_arguments))
        consolidated_perspectives.append(ConsolidatedPerspective(perspective_name=cluster_name, arguments=unique_arguments))
        print(f"  -> Created cluster '{cluster_name}' with {len(unique_arguments)} unique arguments.")
    return consolidated_perspectives

def perspective_clustering_node(state: State) -> dict:
    """
    Analyzes and clusters semantically similar perspectives into a consolidated view.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert at synthesizing and clustering information. Your task is to group a list of perspective summaries into semantically similar clusters.

You will be given a list of perspectives, each with a unique index. You must identify which perspectives are making the same core argument, even if they use different wording.

Instructions:
1.  **Analyze the List**: Read through all the perspective summaries to understand the range of viewpoints.
2.  **Identify Core Themes**: Group perspectives that share a common theme or make a similar central claim.
3.  **Name the Clusters**: For each group, create a short, descriptive, and neutral name for the cluster. This name should represent the core idea of the perspectives within it (e.g., "Economic Impact Concerns," "Focus on Renewable Energy," "Geopolitical Risks").
4.  **Assign Perspectives**: List the original indices of the perspectives that belong to each cluster.

The final output should be a list of these clusters.
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

    article_perspectives_list = state.get("extracted_perspectives")
    print(f"extracted_perspectives: {article_perspectives_list}")

    if not article_perspectives_list:
        print("No perspectives found to consolidate. Skipping clustering node..")
        return {"consolidated_perspectives": []}

    all_perspectives = _flatten_perspectives(article_perspectives_list)
    print(f"all_perspectives: {all_perspectives}")

    if not all_perspectives:
        print("No perspectives found to consolidate. Skipping clustering node..")
        return {"consolidated_perspectives": []}

    perspectives_for_prompt = _format_perspectives_for_prompt(all_perspectives)

    print(f"--- Clustering {len(all_perspectives)} perspectives ---")

    result = chain.invoke({"perspectives": perspectives_for_prompt})

    consolidated_perspectives = _process_clustering_result(result, all_perspectives)

    return {"consolidated_perspectives": consolidated_perspectives}