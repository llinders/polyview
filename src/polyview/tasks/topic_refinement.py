from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from polyview.core.llm_config import llm
from polyview.core.state import State

TOPIC_REFINEMENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert at distilling user requests into clear, concise, and neutral research topics.
Your goal is to analyze a user's message and determine if it contains a researchable topic.

- If the message contains a clear topic, rephrase it as a formal, unbiased statement suitable for kicking off a multi-perspective research task. Return ONLY the refined topic string.
- If the message is ambiguous, a simple greeting, or does not contain a clear request for research, you MUST return the single word "CLARIFY".

Do not add any preamble or explanation to your response.""",
        ),
        ("user", "User message: '{user_message}'"),
    ]
)

def topic_refinement_agent(state: State) -> dict:
    """
    Analyzes the user's message to extract a clear topic or asks for clarification.
    """
    print("--- Refining Topic ---")
    user_message = state["messages"][-1].content

    chain = TOPIC_REFINEMENT_PROMPT | llm | StrOutputParser()

    print(f"Analyzing user message: '{user_message}'")
    analysis_result = chain.invoke({"user_message": user_message})

    if analysis_result.strip().upper() == "CLARIFY":
        print("Clarification needed.")
        return {"topic": "clarify"}
    else:
        print(f"Refined topic: '{analysis_result}'")
        return {"topic": analysis_result}