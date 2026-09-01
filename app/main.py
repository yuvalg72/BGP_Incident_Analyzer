from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .analyzer import DEMO_EVENTS, collect_live, resolve_resource, summarize

BASE = Path(__file__).resolve().parent
app = FastAPI(title="BGP Incident Analyzer", version="1.0.0", docs_url="/api/docs")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class AnalysisRequest(BaseModel):
    resource: str = Field(min_length=2, max_length=64)
    start: datetime
    end: datetime
    projects: list[Literal["ris", "routeviews"]] = ["ris", "routeviews"]
    mode: Literal["auto", "live", "demo"] = "auto"

    @model_validator(mode="after")
    def validate_window(self):
        if self.end <= self.start:
            raise ValueError("End time must be after start time")
        if (self.end - self.start).total_seconds() > 86400 * 7:
            raise ValueError("The maximum query window is seven days")
        if not self.projects:
            raise ValueError("Select at least one data project")
        return self


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(payload: AnalysisRequest):
    try:
        prefix, resolution = await resolve_resource(payload.resource)
        if payload.mode == "demo":
            return summarize(prefix, DEMO_EVENTS, "demo", f"Demonstration dataset; {resolution}")
        try:
            events = await collect_live(prefix, payload.start, payload.end, payload.projects)
            return summarize(prefix, events, "live", f"CAIDA BGPStream; {resolution}")
        except RuntimeError as exc:
            if payload.mode == "live":
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            return summarize(prefix, DEMO_EVENTS, "demo", f"Live source unavailable ({exc}); demonstration dataset shown")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

