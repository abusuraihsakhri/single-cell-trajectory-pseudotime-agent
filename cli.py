"""
Command Line Interface for Single Cell Trajectory Pseudotime Agent.
"""
import argparse
import csv
import json
import math
import os
import sys
from pathlib import Path
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from agents.base import AuditLogger

supervisor = SystemSupervisor(model_provider="mock")


def _safe_resolve_path(path_str: str, must_exist: bool = False) -> Path:
    """Resolve a path safely, preventing directory traversal outside the working directory."""
    cwd = Path.cwd().resolve()
    p = Path(path_str).resolve()
    if must_exist and not p.exists():
        raise FileNotFoundError(f"Input file not found: {path_str}")
    # Ensure the resolved path is within the working directory (prevents path traversal)
    try:
        p.relative_to(cwd)
    except ValueError:
        raise ValueError(
            f"Access denied: path '{path_str}' resolves outside the working directory. "
            "Batch processing is restricted to files within the project directory."
        )
    return p


def _finite_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected a number") from exc
    if not math.isfinite(number):
        raise argparse.ArgumentTypeError("Metric must be finite")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(prog="single-cell-trajectory-pseudotime-agent", description="Single Cell Trajectory Pseudotime Agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Run single task evaluation")
    p_audit.add_argument("--task-id", default="TASK-2026-001")
    p_audit.add_argument("--target", default="KEY-TARGET-01")
    p_audit.add_argument("--primary", type=_finite_float, default=28.5)
    p_audit.add_argument("--secondary", type=_finite_float, default=14.2)
    p_audit.add_argument("--critical", action="store_true")
    p_audit.add_argument("--status", default="DISCORDANT")

    # Chat
    p_chat = subparsers.add_parser("chat", help="System configuration query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="results.csv")

    # Verify Audit
    subparsers.add_parser("verify-audit", help="Verify HMAC audit trail integrity")

    # Serve
    p_serve = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)

    if args.command == "audit":
        payload = SystemTaskPayload(
            task_id=args.task_id,
            target_identifier=args.target,
            primary_metric=args.primary,
            secondary_metric=args.secondary,
            status_descriptor=args.status,
            is_critical_flag=args.critical,
        )
        dossier = supervisor.process_task(payload)
        print("=" * 80)
        print(f"  SINGLE CELL TRAJECTORY PSEUDOTIME AGENT")
        print(f"  Domain: Clinical & Biomedical AI | Standard: CAP / CLSI / ISO Standards")
        print(f"  Dossier ID: {dossier.dossier_id} | Urgency: [{dossier.overall_urgency.value}]")
        print("=" * 80)
        for a in dossier.alerts:
            print(f"\n  [{a.urgency.value}] from {a.origin_worker}:")
            print(f"  Summary: {a.summary}")
            print(f"  Details: {a.technical_details}")
            print(f"  Action:  {a.actionable_remediation}")
        print(f"\n  HMAC-SHA256 Audit Hash: {dossier.audit_hash}")
        print("=" * 80)
        return 0

    if args.command == "chat":
        ans = supervisor.query_supervisory_chat(" ".join(args.query))
        print(f"\n[Single Cell Trajectory Pseudotime Agent Supervisor]:\n{ans}\n")
        return 0

    if args.command == "verify-audit":
        trail = AuditLogger.get_trail()
        valid = AuditLogger.verify_integrity()
        print(f"Audit Trail Blocks: {len(trail)} | Cryptographic Integrity Verified: {valid}")
        return 0 if valid else 1

    if args.command == "batch":
        in_path = _safe_resolve_path(args.input, must_exist=True)
        out_path = _safe_resolve_path(args.output, must_exist=False)
        if in_path == out_path:
            print("Error: Output path must differ from input path.", file=sys.stderr)
            return 1
        with open(in_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)

        out_fields = list(dict.fromkeys(fieldnames + ["overall_urgency", "integrity_status", "total_alerts", "audit_hash"]))
        out_rows = []
        for r in rows:
            try:
                primary = float(r.get("primary_metric", 15.0))
                secondary = float(r.get("secondary_metric", 5.0))
                if not math.isfinite(primary) or not math.isfinite(secondary):
                    raise ValueError("Metrics must be finite")
            except (ValueError, TypeError) as e:
                print(f"Warning: Skipping row with invalid metrics: {r} ({e})")
                continue
            payload = SystemTaskPayload(
                task_id=r.get("task_id", "TASK-01"),
                target_identifier=r.get("target_identifier", "TARGET-01"),
                primary_metric=primary,
                secondary_metric=secondary,
                status_descriptor=r.get("status_descriptor", "NOMINAL"),
                is_critical_flag=str(r.get("is_critical_flag", "")).lower() in ("true", "1", "yes"),
            )
            dossier = supervisor.process_task(payload)
            row_dict = dict(r)
            row_dict["overall_urgency"] = dossier.overall_urgency.value
            row_dict["integrity_status"] = dossier.integrity_status.value
            row_dict["total_alerts"] = dossier.total_alerts
            row_dict["audit_hash"] = dossier.audit_hash
            out_rows.append(row_dict)

        with open(out_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(out_rows)
        print(f"Processed {len(out_rows)} records -> {args.output}")
        return 0

    if args.command == "serve":
        try:
            import uvicorn
            from agents.api import app
            print(f"Starting Single Cell Trajectory Pseudotime Agent API server on http://{args.host}:{args.port}")
            uvicorn.run(app, host=args.host, port=args.port)
        except ImportError:
            print("FastAPI / uvicorn not installed. Run 'pip install fastapi uvicorn'")
            return 1
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
