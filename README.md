# PolyView
PolyView is an application that analyzes news topics from multiple perspectives to provide a holistic view. It
identifies different viewpoints, gathers supporting arguments and facts, and presents a summarized analysis to the user.

## Getting Started

### Prerequisites
- Python (>=3.13, <=4.0)
- [Poetry](https://python-poetry.org/)

### Installation
1. Clone the repository.
2. Install the dependencies:
   ```bash
   poetry install
   ```
3. Setup pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Usage
To set up the environment, run both the FastAPI backend and the React frontend.
```bash
uvicorn polyview.api.main:app --host 0.0.0.0 --port 8000
```
```bash
cd frontend
npm run dev
```
You can then visit https://localhost:5173 to use the webapp.

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

## Architecture
The project is organized into the following key directories:

- `src/polyview/core`: Contains core application state and configuration.
- `src/polyview/agents`: Defines reusable AI agents.
- `src/polyview/tasks`: Holds nodes for specific tasks within the workflows.
- `src/polyview/workflows`: Defines the LangGraph workflows, which can be tested using LangGraph Studio.
