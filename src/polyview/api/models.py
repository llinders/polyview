from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    topic: str


class AnalysisResponse(BaseModel):
    session_id: str
