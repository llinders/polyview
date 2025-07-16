import json

from polyview.core.state import State


def print_state_node(state: State):
    print("\n--- Debug State ---")
    printable_state = {k: v for k, v in state.items() if k != 'raw_articles'}
    printable_state['raw_articles_count'] = len(state.get('raw_articles', []))
    print(json.dumps(printable_state, indent=2, default=str))
    return state