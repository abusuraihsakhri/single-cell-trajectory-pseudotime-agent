# Single Cell Trajectory Pseudotime Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** CAP / CLSI / ISO Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Single Cell Trajectory Pseudotime Agent** is an enterprise-grade analytical platform implementing single-cell KNN graph diffusion pseudotime analysis with branching lineage detection. It provides:

- Multi-worker evaluation pipeline for biomedical metrics
- Zero-PHI outbound data protection (HIPAA Safe Harbor compliant)
- Tamper-evident HMAC-SHA256 audit trail
- REST API and CLI interfaces

---

## 🏗️ Architecture

The project is organized into two main packages:

| Package | Purpose |
|:--------|:--------|
| `agents/` | Enterprise analytical suite with PHI guard, audit logging, specialized workers, and supervisor orchestration |
| `cell_trajectory/` | Frontier domain engine for diffusion pseudotime evaluation |
| `enrichment/` | Extended feature modules for trajectory visualization, gene expression analysis, RNA velocity, and more |

### Key Components

- **`agents/base.py`** — PHIGuard (PHI detection/redaction), AuditTrail (HMAC-SHA256 chained logging)
- **`agents/workers.py`** — Specialized workers: InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
- **`agents/supervisor.py`** — SystemSupervisor orchestrator with multi-worker consensus
- **`agents/api.py`** — FastAPI REST server with `/health`, `/api/audit`, `/api/chat`, `/api/audit/logs`
- **`cell_trajectory/engine.py`** — Core domain engine for diffusion pseudotime evaluation
- **`cell_trajectory/agents.py`** — Sub-agent coordination: KNNGraphBuilderAgent, DiffusionMapEigenvectorAgent, BranchingLineageDetectorAgent

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/single-cell-trajectory-pseudotime-agent.git
cd single-cell-trajectory-pseudotime-agent

# Install core (no external dependencies required for CLI)
pip install -e .

# Optional: Install FastAPI/uvicorn for REST API server
pip install fastapi uvicorn
```

---

## 🚀 CLI Quickstart & Usage

### 1. Run Single Audit
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2 --status DISCORDANT --critical
```

### 2. Interactive Chat
```bash
python cli.py chat "What standard is applied?"
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Parameter Reference

| Flag | Description | Default |
|:-----|:------------|:--------|
| `--task-id` | Unique task identifier | `TASK-2026-001` |
| `--target` | Target specimen/entity identifier | `KEY-TARGET-01` |
| `--primary` | Primary measurement value | `28.5` |
| `--secondary` | Secondary kinetic/confidence score | `14.2` |
| `--critical` | Trigger emergency escalation | `False` |
| `--status` | Status/phenotype descriptor | `DISCORDANT` |

### Input Data Schema (CSV/JSON)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task / case identifier | Required |
| `target_identifier` | Specimen or target identifier | Required |
| `primary_metric` | Primary domain measurement | Required |
| `secondary_metric` | Secondary kinetic/confidence score | Optional (default: 0.0) |
| `is_critical_flag` | Emergency escalation trigger | Optional (default: false) |
| `status_descriptor` | Status code or phenotype | Optional (default: "NOMINAL") |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB patterns, and patient names.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs with integrity verification. Each entry includes the hash of the previous block.
* **Path Traversal Protection:** Batch CSV processing validates that input/output paths remain within the working directory.
* **Secure Defaults:** Audit signing key auto-generated via `secrets.token_hex()` if `AUDIT_SECRET_KEY` env var is not set (with runtime warning).
* **Input Validation:** All metric inputs validated for correct types; malformed CSV rows are skipped with warnings.

### Environment Variables

| Variable | Purpose | Required |
|:---------|:--------|:---------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC-SHA256 audit signing | No (auto-generated if unset) |
| `MODEL_PROVIDER` | LLM provider for chat (mock, ollama, claude, openai) | No (default: mock) |

---

## 🧪 Testing & Verification

### Run Automated Test Suite
```bash
pytest -v
```

### Run with Coverage
```bash
pip install pytest-cov
pytest -v --cov=agents --cov=cell_trajectory --cov=enrichment
```

### Execute Batch Simulation
```bash
python simulator.py 100
```

### Security Audit
```bash
python -c "
from agents.base import PHIGuard, AuditLogger
assert AuditLogger.verify_integrity() is True
PHIGuard.assert_no_phi('Safe text without PHI')
print('Security Audit Passed!')
"
```

---

## 🐳 Container Deployment

### Docker Compose (Recommended)
```bash
# Set a production audit key
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker-compose up --build
```

### Docker Direct
```bash
docker build -t single-cell-trajectory-pseudotime-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key single-cell-trajectory-pseudotime-agent
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check and system metadata |
| GET | `/metrics` | Prometheus operational metrics |
| POST | `/api/audit` | Submit task for evaluation |
| POST | `/api/chat` | Supervisory conversational query |
| GET | `/api/audit/logs` | Retrieve and verify HMAC audit trail |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Dr. Abu Suraih Sakhri** — [GitHub](https://github.com/abusuraihsakhri)
