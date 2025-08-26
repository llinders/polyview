import uvicorn

from polyview.core.logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    uvicorn.run(app="polyview.api.main:app", host="0.0.0.0", port=8000, reload=True)
