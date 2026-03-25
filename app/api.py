from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.models import Alert
from app.runtime import triage_from_inputs


class TriageRequest(BaseModel):
    alert_id: str = Field(..., examples=["ALERT-2026-00110"])
    source_ip: str = Field(..., examples=["185.193.88.42"])
    destination_host: str = Field(..., examples=["FIN-WS-014"])
    user: str = Field(..., examples=["jane.doe"])
    summary: str = Field(..., examples=["Multiple failed logons followed by remote execution"])
    logs_text: Optional[str] = Field(default=None)
    logs_path: Optional[str] = Field(default=None)


app = FastAPI(title="Cyber-Defense Triage API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/triage")
def triage(request: TriageRequest) -> Dict[str, Any]:
    logs = request.logs_text

    if not logs and request.logs_path:
        logs_file = Path(request.logs_path)
        if not logs_file.exists():
            raise HTTPException(status_code=400, detail=f"logs_path not found: {request.logs_path}")
        logs = logs_file.read_text(encoding="utf-8")

    if not logs:
        raise HTTPException(status_code=400, detail="Provide either logs_text or logs_path")

    alert = Alert(
        alert_id=request.alert_id,
        source_ip=request.source_ip,
        destination_host=request.destination_host,
        user=request.user,
        summary=request.summary,
        raw=request.model_dump(),
    )

    try:
        result = triage_from_inputs(alert, logs)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Triage failed: {exc}") from exc

    return result.__dict__
