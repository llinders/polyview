from typing import List, Dict

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.state import State, ConsolidatedPerspective, ExtractedPerspective


class PerspectiveCluster(BaseModel):
    """A single cluster of similar perspectives."""
    cluster_name: str = Field(description="A short, descriptive name for the cluster (e.g., 'Techno-Optimist').")
    perspective_indices: List[int] = Field(description="The list of indices corresponding to the original perspectives that belong to this cluster.")

class ClusteringResult(BaseModel):
    """The result of clustering all perspectives."""
    clusters: List[PerspectiveCluster]

def _flatten_perspectives(perspectives_by_article: Dict[str, List[Dict]]) -> List[ExtractedPerspective]:
    """Flattens a dictionary of perspective lists into a single list of ExtractedPerspective objects."""
    all_perspectives: List[ExtractedPerspective] = []
    for article_id, perspective_list in perspectives_by_article.items():
        for p_data in perspective_list:
            if isinstance(p_data, dict):
                all_perspectives.append(ExtractedPerspective(**p_data))
            else:
                all_perspectives.append(p_data)
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

def perspective_clustering_node(state: State) -> List[ConsolidatedPerspective]:
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

    perspectives_by_article = state.get("extracted_perspectives")

    if not perspectives_by_article:
        print("No perspectives found to consolidate. Skipping clustering node..")
        return {"consolidated_perspectives": []}

    all_perspectives = _flatten_perspectives(perspectives_by_article)

    if not all_perspectives:
        print("No perspectives found to consolidate. Skipping clustering node..")
        return {"consolidated_perspectives": []}

    perspectives_for_prompt = _format_perspectives_for_prompt(all_perspectives)

    print(f"--- Clustering {len(all_perspectives)} perspectives ---")

    result = chain.invoke({"perspectives": perspectives_for_prompt})

    consolidated_perspectives = _process_clustering_result(result, all_perspectives)

    return {"consolidated_perspectives": consolidated_perspectives}