from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from polyview.core.llm_config import llm
from polyview.core.logging import get_logger
from polyview.core.state import (
    ArticlePerspectives,
    ConsolidatedPerspective,
    ExtractedPerspective,
    FinalPerspective,
    State,
)

logger = get_logger(__name__)


class PerspectiveCluster(BaseModel):
    """A single cluster of similar perspectives."""

    cluster_name: str = Field(
        description="A short, descriptive name for the cluster (e.g., 'Scientific Consensus', 'Techno-Optimist', "
        "'Skeptical/Contrarian', 'Justice-Oriented', 'Economic Impact Concerns', 'Geopolitical Risks', "
        "'Conservative', 'Liberal', etc. The name should immediately convey the essence of the perspective."
    )
    perspective_indices: list[int] = Field(
        description="The list of indices corresponding to the original perspectives that belong to this cluster."
    )


class ClusteringResult(BaseModel):
    """The result of clustering all perspectives."""

    clusters: list[PerspectiveCluster]


def _flatten_perspectives(
    article_perspectives_list: list[ArticlePerspectives],
) -> list[ExtractedPerspective]:
    """
    Flattens a list of ArticlePerspectives into a single list of ExtractedPerspective objects.
    This function handles cases where the input list contains dictionaries instead of Pydantic objects.
    """
    all_perspectives: list[ExtractedPerspective] = []
    # The data from the state can be a list of dicts, so we parse them into ArticlePerspectives objects.
    for item in article_perspectives_list:
        if isinstance(item, dict):
            article_p = ArticlePerspectives.model_validate(item)
        else:
            article_p = item  # Assume it's already an ArticlePerspectives object
        all_perspectives.extend(article_p.perspectives)
    return all_perspectives


def _format_perspectives_for_prompt(
    all_perspectives: list[ExtractedPerspective],
) -> list[dict]:
    """Formats perspectives for the LLM prompt, including their original index and summary."""
    return [
        {"index": i, "summary": p.perspective_summary}
        for i, p in enumerate(all_perspectives)
    ]


def _create_synthesis_prompt(
    cluster_name: str, aggregated_narratives: list[str]
) -> str:
    """Creates a prompt for synthesizing a narrative from a list of narratives."""
    synthesis_prompt = ChatPromptTemplate.from_template(
        "Create a brief, synthesized narrative (1-2 paragraphs) from the following collected narratives for the perspective: '{cluster_name}'.\n\n---\n{narratives}\n---"
    )
    synthesis_chain = synthesis_prompt | llm
    return synthesis_chain.invoke(
        {"cluster_name": cluster_name, "narratives": "\n\n".join(aggregated_narratives)}
    ).content


def _process_clustering_result(
    result: ClusteringResult,
    all_perspectives: list[ExtractedPerspective],
    existing_perspectives: list[FinalPerspective],
    iteration: int,
) -> list[ConsolidatedPerspective]:
    """Processes the clustering result to consolidate arguments for each cluster."""
    consolidated_perspectives: list[ConsolidatedPerspective] = []

    for cluster in result.clusters:
        cluster_name = cluster.cluster_name
        aggregated_arguments = []
        aggregated_narratives = []
        supporting_evidence = []

        # Check if the cluster corresponds to an existing perspective
        existing_perspective: FinalPerspective | None = next(
            (p for p in existing_perspectives if p.perspective_name == cluster_name),
            None,
        )

        if existing_perspective:
            logger.info(
                f"Updating existing perspective '{cluster_name}' with new article perspectives."
            )
            # If it is an existing perspective, we add the new arguments to it
            aggregated_arguments.extend(existing_perspective.core_arguments)
            aggregated_narratives.append(existing_perspective.narrative)
            supporting_evidence.extend(existing_perspective.supporting_evidence)
        elif not existing_perspective and iteration > 1:
            logger.info(f"Creating new perspective '{cluster_name}' from new articles.")

        for index in cluster.perspective_indices:
            if 0 <= index < len(all_perspectives):
                perspective = all_perspectives[index]
                aggregated_arguments.extend(perspective.key_arguments)
                aggregated_narratives.append(perspective.contextual_narrative)
                supporting_evidence.extend(perspective.evidence_provided)

        preliminary_synthesis = _create_synthesis_prompt(
            cluster_name, aggregated_narratives
        )

        consolidated_perspectives.append(
            ConsolidatedPerspective(
                perspective_name=cluster_name,
                aggregated_arguments=list(dict.fromkeys(aggregated_arguments)),
                aggregated_narratives=list(dict.fromkeys(aggregated_narratives)),
                supporting_evidence=list(dict.fromkeys(supporting_evidence)),
                preliminary_synthesis=preliminary_synthesis,
            )
        )
        logger.info(
            f"Processed cluster '{cluster_name}' with {len(aggregated_arguments)} arguments."
        )
    return consolidated_perspectives


def perspective_clustering_node(state: State) -> dict:
    """
    Analyzes and clusters semantically similar perspectives into a consolidated view.
    On the first run, it creates new clusters from the extracted perspectives.
    On subsequent runs, it can cluster new perspectives into existing ones.
    """
    iteration = state.get("iteration", 1)
    raw_existing_perspectives = state.get("final_perspectives", [])
    existing_perspectives = [
        FinalPerspective.model_validate(p) if isinstance(p, dict) else p
        for p in raw_existing_perspectives
    ]

    system_prompt = """You are an advanced analytical AI specializing in synthesizing diverse viewpoints into coherent, distinct perspectives. Your primary goal is to group a given list of individual perspective summaries into semantically similar clusters. Each cluster should represent a unique, meaningful, and well-defined core argument or viewpoint on the topic.

Crucial Guidelines for Clustering:
1.  **Holistic View:** Aim to create clusters that collectively offer a comprehensive and balanced understanding of the topic, covering the main schools of thought or arguments.
2.  **Distinctness:** Each cluster must represent a clearly distinguishable perspective. Avoid creating clusters that are too broad, vague, or overlap significantly. Conversely, do not scatter closely related perspectives into too many separate, minor clusters.
3.  **Core Argument Focus:** Identify perspectives that share the *same fundamental argument or central claim*, even if expressed with different wording or nuances.
4.  **Cluster Naming:** For each identified cluster, provide a concise, descriptive, and neutral name that accurately captures its core idea. The name should immediately convey the essence of the perspective.
5.  **Assignment:** Accurately assign the original indices of all perspectives that belong to each cluster."""

    if iteration > 1 and existing_perspectives:
        human_prompt = """You have already identified the following perspectives:

```json
{existing_perspectives}
```

Now, please cluster the following new perspectives. You can either assign them to one of the existing perspective clusters or create new ones if they don't fit.

New perspectives to cluster:
```json
{perspectives}
```"""
    else:
        human_prompt = """Please cluster the following perspectives:
```json
{perspectives}
```"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
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

    if iteration > 1 and existing_perspectives:
        existing_perspectives_json = [
            p.model_dump_json(indent=2) for p in existing_perspectives
        ]
        result = chain.invoke(
            {
                "perspectives": perspectives_for_prompt,
                "existing_perspectives": existing_perspectives_json,
            }
        )
    else:
        result = chain.invoke({"perspectives": perspectives_for_prompt})

    consolidated_perspectives = _process_clustering_result(
        result, all_perspectives, existing_perspectives, iteration
    )

    return {"consolidated_perspectives": consolidated_perspectives}
