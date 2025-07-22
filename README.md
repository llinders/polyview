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

## Usage
To test and run the workflows, use LangGraph Studio:

```bash
poetry run langgraph dev
```

## Testing
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
