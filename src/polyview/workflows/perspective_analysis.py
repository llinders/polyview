from langgraph.graph import StateGraph

from polyview.core.state import State

workflow = StateGraph(State)

## First run
# 1. Individual perspective identification
# 2. Perspective clustering & grouping arguments/facts (focus only on perspective and maybe a few arguments for more context and come up with a few core perspectives)
# 3. Perspective elaboration (synthesizing the core of all aggregated arguments)

## Other runs
# Instead of just creating a new perspective group from the new articles, we should check if they can be
# clustered into existing perspectives. If they can group them in there and review perspective elaboration if
# new arguments are presented. Otherwise: create a new perspective