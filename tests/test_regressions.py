"""Regression tests for packaging, API safety, and batch processing."""
import math

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.api import app
from agents.base import AuditLogger, AuditTrail
from agents.models import SystemTaskPayload
from cli import main


client = TestClient(app)


def test_metrics_reject_nonfinite():
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T1", target_identifier="KEY-1", primary_metric=value)
        with pytest.raises(ValidationError):
            SystemTaskPayload(task_id="T1", target_identifier="KEY-1", primary_metric=1, secondary_metric=value)


def test_metric_length_validation():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="X" * 129, target_identifier="KEY-1", primary_metric=1)


def test_api_guard_returns_client_error():
    result = client.post("/api/audit", json={
        "task_id": "MRN-12345", "target_identifier": "KEY-01", "primary_metric": 10.0
    })
    assert result.status_code == 400
    assert "identifier" in result.json()["detail"].lower()
    result = client.post("/api/chat", json={"query": "john@example.com"})
    assert result.status_code == 400


def test_audit_logs_require_token(monkeypatch):
    monkeypatch.delenv("AUDIT_LOGS_TOKEN", raising=False)
    assert client.get("/api/audit/logs").status_code == 404
    monkeypatch.setenv("AUDIT_LOGS_TOKEN", "a-test-token")
    assert client.get("/api/audit/logs").status_code == 403
    assert client.get("/api/audit/logs", headers={"Authorization": "Bearer wrong"}).status_code == 403
    result = client.get("/api/audit/logs", headers={"Authorization": "Bearer a-test-token"})
    assert result.status_code == 200
    assert result.json()["verified"] is True


def test_audit_trail_returns_defensive_copy():
    log = AuditTrail(secret_key="test-key")
    log.log("system", "test", "event", {"value": 1})
    snapshots = log.get_trail()
    snapshots[0]["payload_hash"] = "changed"
    assert log.verify_integrity() is True


def test_batch_prevents_input_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = "task_id,target_identifier,primary_metric\\nA,B,12\\n"
    file = tmp_path / "data.csv"
    file.write_text(payload, encoding="utf-8")
    assert main(["batch", "-i", "data.csv", "-o", "data.csv"]) == 1
    assert file.read_text(encoding="utf-8") == payload


def test_batch_rejects_nonfinite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data.csv").write_text(
        "task_id,target_identifier,primary_metric,secondary_metric\\n"
        "A,B,nan,1\\nC,D,12,1\\n", encoding="utf-8"
    )
    assert main(["batch", "-i", "data.csv", "-o", "output.csv"]) == 0
    output = (tmp_path / "output.csv").read_text(encoding="utf-8")
    assert "C,D," in output
    assert "A,B," not in output
