# Single Cell Trajectory Pseudotime Agent

A Python project with **two distinct workflows**: an experimental diffusion-map pseudotime estimator for small numeric single-cell feature matrices, and a pre-existing rule-based metric audit service. These workflows do not share a biological inference model.

## Scientific workflow: pseudotime

The `cell_trajectory.pseudotime.diffusion_pseudotime` function constructs a symmetric adaptive-Gaussian **k-nearest-neighbor graph**, forms a Markov diffusion operator, and estimates root-relative pseudotime from its nonstationary eigenmodes with `lambda / (1 - lambda)` weighting. Output is scaled from 0 (specified root) to 1 (most distant sampled cell).

This is an **exploratory spectral diffusion-pseudotime approximation**, not a validated reimplementation of Scanpy/Palantir/DPT, RNA velocity, lineage bifurcation detection, or a clinical decision tool. Trajectory interpretation depends on the selected root, embedding, and preprocessing. No differential expression, uncertainty quantification, or biological validation is performed.

**Limits:** 3–300 cells, 1–50 numeric features, a single connected undirected kNN graph, and a dense `O(n^3)` eigendecomposition. Input must be scaled/preprocessed appropriately beforehand; raw counts are not normalized by the tool. Disconnected graphs produce an error rather than arbitrary pseudotime.

### Installation and example

Requires Python 3.9+.

```bash
git clone https://github.com/abusuraihsakhri/single-cell-trajectory-pseudotime-agent.git
cd single-cell-trajectory-pseudotime-agent
python -m pip install -e ".[trajectory]"

single-cell-agent pseudotime \
  --input example_cells.csv --output pseudotime.csv \
  --root-cell C0 --neighbors 2 --components 7
```

The input CSV has `cell_id` as its first header and one or more numeric feature columns:

```csv
cell_id,feature_1,feature_2
C0,0,0
C1,1,0
C2,2,0
```

The output is `cell_id,pseudotime` in input order. Duplicate IDs, missing values, non-finite numbers, invalid roots, and unsupported graph sizes are rejected. Keep input and output paths distinct.

### Rule-based metric audit (legacy workflow)

The existing `agents/` API and `cell_trajectory/` agent classes apply fixed thresholds and descriptor-keyword rules. **These are not pseudotime calculations**, do not implement a clinical standard, and should not be interpreted as validated biomedical advice. Both interfaces remain available for compatibility.

```bash
python -m pip install -e ".[api]"
single-cell-agent audit --task-id T1 --primary 28 --secondary 14 --status DISCORDANT
single-cell-agent batch -i sample.csv -o results.csv
single-cell-agent verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

On a running local server:
- `GET /health` and `GET /metrics` report status and in-memory counts.
- `POST /api/audit` evaluates a metric payload with the same rules.
- `POST /api/chat` returns a deterministic mock response, not a live language-model analysis.
- `GET /api/audit/logs` is disabled unless `AUDIT_LOGS_TOKEN` is set; access then requires `Authorization: Bearer <token>`.

The original `single-cell-trajectory-pseudotime-engine` console command remains mapped to the legacy `cell_trajectory.cli` rule engine for compatibility; `cell-trajectory-frontier` is an additional alias. The new `single-cell-agent` command runs the root CLI and scientific subcommand.

### Browser demo and GitHub Pages

`web/index.html` is a standalone, responsive **browser-only preview of the metric threshold rules**. It makes no network requests, does not sign audit entries, and **does not run Python or estimate pseudotime**. Use synthetic identifiers; do not enter patient or confidential data. A GitHub Actions workflow publishes `web/` to Pages when Pages is configured for GitHub Actions. Browser execution is separate from the Python API.

## Security and data handling

- The audit API screens some identifier patterns. This is **not reliable PHI de-identification or HIPAA compliance**. Do not submit patient data.
- HMAC-SHA256 signing applies to **in-memory audit records**. Supply `AUDIT_SECRET_KEY` for key consistency across restarts; the audit history itself is not persisted.
- Set `AUDIT_LOGS_TOKEN` to restrict log retrieval. Other API endpoints are not authenticated; deploy behind appropriate authentication and network controls for non-demo use.
- The metric batch CLI restricts paths to its current working directory, and refuses overwriting the input.
- Scientific CSV processing runs locally; no upstream network service is used. Neither browser mode nor the scientific CLI sends data to a provider.

## Development and testing

```bash
python -m pip install -e ".[api,test,trajectory]"
python -m pytest -q
node --test tests/test_web_ui.mjs
python -m compileall -q agents cell_trajectory cli.py enrichment.py simulator.py
```

GitHub Actions runs the Python test matrix and browser JavaScript smoke tests. The Dockerfile and Compose service run the legacy FastAPI audit server, not the scientific CLI. For Compose, set a non-default `AUDIT_SECRET_KEY` in the environment.

## Technology and compatibility

Python 3.9+, NumPy (optional scientific calculations), Pydantic 2, optional FastAPI/Uvicorn, standard-library CSV, and a plain HTML/CSS/JavaScript browser demo. The browser demo is designed for modern Chromium, Firefox, and Safari; automated browser coverage is limited to JavaScript execution tests.

## License

MIT — see [LICENSE](LICENSE).
