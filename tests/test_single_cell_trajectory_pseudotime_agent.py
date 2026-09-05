"""
Automated Pytest Test Suite for Single Cell Trajectory Pseudotime Agent.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main, _safe_resolve_path


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_phi_guard_redaction():
    redacted = PHIGuard.redact_phi("Contact patient at 555-123-4567 or test@example.com")
    assert "555-123-4567" not in redacted
    assert "test@example.com" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_supervisor_blocks_phi_in_task_id():
    """Verify that supervisor rejects task IDs containing PHI."""
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="MRN-12345",
        target_identifier="KEY-01",
        primary_metric=10.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    with pytest.raises(SecurityException):
        supervisor.process_task(payload)


def test_audit_trail_integrity_tampering():
    """Verify that tampering with audit trail is detected."""
    trail = AuditTrail(secret_key="test-key-for-integrity")
    trail.log("test", "tier", "event", {"data": "value1"})
    trail.log("test", "tier", "event", {"data": "value2"})
    assert trail.verify_integrity() is True

    # Simulate tampering
    if trail.logs:
        trail.logs[0]["payload_hash"] = "tampered"
    assert trail.verify_integrity() is False


def test_safe_resolve_path_blocks_traversal():
    """Verify that path traversal attempts are blocked."""
    with pytest.raises(ValueError, match="Access denied"):
        _safe_resolve_path("../../etc/passwd")

    with pytest.raises(ValueError, match="Access denied"):
        _safe_resolve_path("/etc/passwd")


def test_safe_resolve_path_allows_local():
    """Verify that local paths are allowed."""
    p = _safe_resolve_path("sample.csv", must_exist=True)
    assert p.exists()
    assert p.name == "sample.csv"


def test_audit_trail_ephemeral_key_generation():
    """Verify that AuditTrail generates ephemeral key when none provided."""
    import warnings
    # Clear env var to test ephemeral generation
    import os
    old_key = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail(secret_key=None)
            assert len(w) == 1
            assert "AUDIT_SECRET_KEY not set" in str(w[0].message)
            assert len(trail.secret_key) > 0
    finally:
        if old_key:
            os.environ["AUDIT_SECRET_KEY"] = old_key
