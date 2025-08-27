from typing import Any

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    topic: str


class AnalysisResponse(BaseModel):
    session_id: str


class SummarizeRequest(BaseModel):
    final_perspectives: list[dict[str, Any]]
