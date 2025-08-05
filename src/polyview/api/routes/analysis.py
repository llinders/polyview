import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect

from polyview.api.models import AnalysisRequest, AnalysisResponse
from polyview.workflows.research_workflow import graph as research_workflow_graph

router = APIRouter()

# In-memory storage for active WebSocket connections and message queues
active_connections: dict[str, list[WebSocket]] = {}
session_message_queues: dict[str, asyncio.Queue] = {}


async def run_analysis_workflow(session_id: str, topic: str):
    """
    Runs the LangGraph analysis workflow and sends updates via WebSocket.
    """
    queue = session_message_queues.get(session_id)
    if not queue:
        return

    final_state = {}

    try:
        await queue.put(
            {"type": "status", "message": f"Starting analysis for topic: '{topic}'"}
        )

        # Initial state for the workflow
        initial_state = {"topic": topic, "iteration": 0}

        # Stream the workflow execution
        async for state in research_workflow_graph.astream(initial_state):
            final_state = state  # Capture the latest state
            current_node = list(state.keys())[-1]  # Get the last node that ran

            # Send a status update for each node completion
            await queue.put(
                {
                    "type": "status",
                    "message": f"Completed step: {current_node.replace('_', ' ').title()}",
                }
            )

            if "iteration" in state:
                await queue.put(
                    {
                        "type": "status",
                        "message": f"Current iteration: {state['iteration']}",
                    }
                )
            if "raw_articles" in state:
                await queue.put(
                    {
                        "type": "status",
                        "message": f"Articles found: {len(state['raw_articles']) if state['raw_articles'] else 0}",
                    }
                )
            if "final_perspectives" in state:
                await queue.put(
                    {
                        "type": "status",
                        "message": f"Perspectives identified: {len(state['final_perspectives']) if state['final_perspectives'] else 0}",
                    }
                )

            # TODO: Possibly add more specific in between updates here such as summaries to display partial results

        await queue.put({"type": "status", "message": "Analysis complete!"})
        await queue.put(
            {
                "type": "final_result",
                "data": {
                    "topic": topic,
                    "summary": final_state.get("summary", "No summary available."),
                    "perspectives": [
                        p.model_dump()
                        for p in final_state.get("final_perspectives", [])
                    ],
                },
            }
        )

    except Exception as e:
        await queue.put({"type": "error", "message": f"Analysis failed: {str(e)}"})
    finally:
        await queue.put({"type": "end_of_stream"})


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_topic(request: AnalysisRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    session_message_queues[session_id] = asyncio.Queue()
    active_connections[session_id] = []

    background_tasks.add_task(run_analysis_workflow, session_id, request.topic)
    return AnalysisResponse(session_id=session_id)


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in active_connections:
        # If session_id is not known, close connection or handle error
        await websocket.close(code=1008)  # Policy Violation
        return

    active_connections[session_id].append(websocket)
    queue = session_message_queues[session_id]

    try:
        while True:
            # Wait for messages from the analysis workflow
            message = await queue.get()
            if message["type"] == "end_of_stream":
                break
            await websocket.send_json(message)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Clean up connection
        if websocket in active_connections[session_id]:
            active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            # If no more active connections for this session, clean up queue
            del session_message_queues[session_id]
            del active_connections[session_id]
        await websocket.close()
