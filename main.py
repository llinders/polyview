from dotenv import load_dotenv
load_dotenv()

import json
from langchain_core.messages import HumanMessage

from agents.search_agent import run_search_queries
from agents.perspective_identification import perspective_identification_agent
from core.state import State

if __name__ == "__main__":
    # --- 1. Initial State with Manual Queries ---
    topic = "The debate around using nuclear energy to combat climate change."
    manual_queries = [
        "arguments for and against nuclear energy as a solution to climate change",
        "economic cost of nuclear power plants vs renewable energy",
        "safety concerns and waste disposal of modern nuclear reactors",
        "public opinion on nuclear energy 2024"
    ]

    current_state: State = {
        "messages": [HumanMessage(content=f"Research topic: {topic}")],
        "topic": topic,
        "search_queries": manual_queries,
        "raw_articles": [],
        "iteration": 1,
        "identified_perspectives": [],
        "missing_perspectives": [],
    }
    print("--- 1. Kicking off with initial state ---")
    print(f"Topic: {current_state['topic']}")
    print(f"Manual Queries: {current_state['search_queries']}")


    # --- 2. Run Live Web Searches via the Search Agent ---
    print("\n--- 2. Running Live Web Searches ---")
    search_update = run_search_queries(current_state)
    current_state.update(search_update)


    # --- 3. Run Perspective Identification Agent ---
    print("\n--- 3. Running Perspective Identification Agent ---")
    perspective_update = perspective_identification_agent(current_state)
    current_state.update(perspective_update)


    # --- 4. Final State ---
    print("\n--- 4. Final State after Full Pipeline ---")
    print(json.dumps(current_state, default=lambda o: o.dict() if hasattr(o, 'dict') else str, indent=2))