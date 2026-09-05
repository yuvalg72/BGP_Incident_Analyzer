from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .analyzer import (
    DEMO_EVENTS,
    DEMO_PREFIX,
    ResourceTarget,
    collect_live,
    parse_resource,
    resolve_resource,
    summarize,
)

BASE = Path(__file__).resolve().parent
APP_VERSION = "0.2.0"
app = FastAPI(
    title="BGP Incident Analyzer",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; "
        "frame-ancestors 'none'; form-action 'self'",
    )
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    )
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource: str = Field(min_length=2, max_length=64)
    start: datetime
    end: datetime
    projects: list[Literal["ris", "routeviews"]] = Field(
        default_factory=lambda: ["ris", "routeviews"]
    )
    mode: Literal["auto", "live", "demo"] = "live"

    @field_validator("start", "end")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Start and end timestamps must include a timezone")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_window(self):
        if self.end <= self.start:
            raise ValueError("End time must be after start time")
        if (self.end - self.start).total_seconds() > 86400 * 7:
            raise ValueError("The maximum query window is seven days")
        if not self.projects:
            raise ValueError("Select at least one data project")
        if len(set(self.projects)) != len(self.projects):
            raise ValueError("Data projects must not contain duplicates")
        return self


def _attach_query_context(
    result: dict[str, Any],
    target: ResourceTarget,
    *,
    live_filter_used: bool,
) -> dict[str, Any]:
    result["query"] = {
        "requested_resource": target.requested_resource,
        "resolved_prefix": target.display_prefix,
        "bgp_filter": target.bgp_filter if live_filter_used else None,
    }
    return result


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/health", include_in_schema=False)
async def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/ready", include_in_schema=False)
async def ready():
    if not shutil.which("bgpreader"):
        raise HTTPException(status_code=503, detail="bgpreader is not available")
    return {"status": "ready", "version": APP_VERSION, "bgpreader": True}


@app.post("/api/analyze")
async def analyze(payload: AnalysisRequest):
    try:
        parsed_target = parse_resource(payload.resource)
        if payload.mode == "demo":
            return _attach_query_context(
                summarize(
                    DEMO_PREFIX,
                    DEMO_EVENTS,
                    "demo",
                    (
                        f"Demonstration dataset for {DEMO_PREFIX}; requested resource "
                        f"was {parsed_target.requested_resource}; no live BGP query was run"
                    ),
                ),
                parsed_target,
                live_filter_used=False,
            )

        target = await resolve_resource(payload.resource)
        try:
            events = await collect_live(
                target.bgp_filter, payload.start, payload.end, payload.projects
            )
            return _attach_query_context(
                summarize(
                    target.display_prefix,
                    events,
                    "live",
                    f"CAIDA BGPStream; {target.resolution}",
                ),
                target,
                live_filter_used=True,
            )
        except RuntimeError as exc:
            if payload.mode == "live":
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            return _attach_query_context(
                summarize(
                    DEMO_PREFIX,
                    DEMO_EVENTS,
                    "demo",
                    (
                        f"Live source unavailable ({exc}); demonstration dataset for "
                        f"{DEMO_PREFIX} shown instead of live results for "
                        f"{target.requested_resource}"
                    ),
                ),
                target,
                live_filter_used=False,
            )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
