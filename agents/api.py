"""HTTP API for rule-based metric auditing (not trajectory inference)."""
import hmac
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from .base import AuditLogger, SecurityException
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Single Cell Trajectory Pseudotime Agent: Metric Audit API",
    description="Rule-based metric screening; does not calculate diffusion pseudotime.",
    version="2.0.1",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "single-cell-trajectory-pseudotime-agent", "mode": "rule-based metric screening", "version": "2.0.1"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "audit_chain_valid": AuditLogger.verify_integrity(),
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        return supervisor.process_task(payload).to_dict()
    except SecurityException:
        raise HTTPException(status_code=400, detail="Input contains a prohibited identifier") from None


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        return {"response": supervisor.query_supervisory_chat(req.query)}
    except SecurityException:
        raise HTTPException(status_code=400, detail="Input contains a prohibited identifier") from None


@app.get("/api/audit/logs")
def api_audit_logs(authorization: Optional[str] = Header(default=None)):
    # Audit entries can carry sensitive operational metadata. Never publish
    # them anonymously; disable this endpoint until a token is configured.
    token = os.environ.get("AUDIT_LOGS_TOKEN")
    if not token:
        raise HTTPException(status_code=404, detail="Audit log access is disabled")
    expected = f"Bearer {token}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=403, detail="Invalid audit log credentials")
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
