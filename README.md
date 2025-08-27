# PolyView
PolyView is an application that analyzes news topics from multiple perspectives to provide a holistic view. It
identifies different viewpoints, gathers supporting arguments and facts, and presents a summarized analysis to the user.

https://github.com/user-attachments/assets/cfe15398-d9ea-40b5-a909-e23a23fe756b

## Getting Started

### Prerequisites
- Python (>=3.13, <=4.0)
- [Poetry](https://python-poetry.org/)

### Installation
1. Clone the repository.
2. Install Python project dependencies:
   ```bash
   poetry install
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. Setup pre-commit hooks:
   ```bash
   poetry run pre-commit install
   ```

## Local setup & usage
Follow these steps to set up the environment and run both the FastAPI backend and the React frontend locally.
**FastAPI backend**
```bash
poetry run python src/polyview/main.py
```
or run the following in a shell: 
```bash
poetry run uvicorn polyview.api.main:app --host 0.0.0.0 --port 8000
```

**React frontend**
```bash
cd frontend
npm run dev
```

You can then visit https://localhost:5173 to use the webapp.

## Architecture Overview
### 1. Frontend (React + TypeScript)
A responsive user interface built with React and TypeScript, using Vite.
-   Communicates with the backend via a REST API to start the analysis and a WebSocket for real-time progress updates.

### 2. Backend (Python + FastAPI)
An asynchronous backend built with FastAPI. 
- Exposes a REST API to initiate the analysis and a WebSocket to stream progress updates.

### 3. AI Core (LangGraph)
The "brain" of the application, where the analysis takes place. It is built with LangGraph to create a stateful, graph-based workflow.
-   Features an autonomous search agent that gathers and filters information from the web.
-   Uses a stateful graph to orchestrate a series of specialized tasks that perform perspective identification, clustering, and synthesis.
<br>
![LangGraph Workflow](assets/langgraph-workflow.png)

### High-Level Data Flow
1.  The **Frontend** sends a topic to the **Backend**'s REST API.
2.  The **Backend** initiates the **AI Core's** analysis workflow in the background and establishes a WebSocket connection with the frontend.
3.  The **AI Core** executes its graph, starting with the **Search Agent** and proceeding through the analysis tasks.
4.  Progress is streamed back to the **Frontend** via the WebSocket in real-time.
5.  The final, structured report is delivered to the **Frontend** for display.

## Testing
### LangGraph Studio
To test, run, and debug the workflows, use LangGraph Studio:

```bash
poetry run langgraph dev
```

### Automated tests
The project contains both unit and integration tests. The test directory structure mirrors the `src` directory:
- **Unit Tests:** Located in `tests/`. For a source file like `src/polyview/tasks/some_task.py`, the corresponding unit
  test is `tests/tasks/test_some_task.py`.
- **Integration Tests:** Located in `tests/integration/`. These tests are marked with the `integration` marker and are
  excluded by default.

Use the following commands to run the tests:
- **Run unit tests (default):**
  ```bash
  poetry run pytest
  ```
- **Run only integration tests:**
  ```bash
  poetry run pytest -m integration
  ```
- **Run all tests:**
   ```bash
   poetry run pytest -m "integration or not integration"
   ```