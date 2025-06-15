from src.agents.graph import graph

if __name__ == "__main__":

    print("--- Starting Test Workflow ---")
    graph.invoke(
        {
        "topic": "The conflict between Israel and Palastine",
        "search_queries": [
            "Differing perspectives on the Israel-Palestine conflict: Israeli vs Palestinian narratives",
            "Historical timeline of the Israel-Palestine conflict since 1948",
            "What are the main political and territorial disputes between Israel and Palestine?",
            "Role of international actors in the Israel-Palestine conflict (UN, US, Arab League, etc.)"
        ],
        "messages": []
        }
    )
    print("\n--- Test Workflow Finished ---")