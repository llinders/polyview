from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from polyview.api.routes import analysis

app = FastAPI(
    title="PolyView API",
    description="API for PolyView, a news analysis application providing multiple perspectives.",
    version="0.2.0",
)

# CORS configuration
origins = [
    "http://localhost:3000",  # React app default port
    "http://localhost:8000",  # FastAPI app itself
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])


@app.get("/")
async def read_root():
    return {"message": "PolyView API is running!"}
