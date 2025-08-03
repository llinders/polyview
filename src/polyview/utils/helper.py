import json

from polyview.core.logging import get_logger
from polyview.core.state import State

logger = get_logger(__name__)


def print_state_node(state: State):
    logger.debug("--- Debug State ---")
    printable_state = {k: v for k, v in state.items() if k != "raw_articles"}
    printable_state["raw_articles_count"] = len(state.get("raw_articles", []))
    logger.debug(json.dumps(printable_state, indent=2, default=str))
    return state
