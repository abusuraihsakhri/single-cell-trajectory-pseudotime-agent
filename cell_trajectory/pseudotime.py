"""Small-data diffusion-map pseudotime estimator for numeric cell embeddings.

Exploratory method, not lineage inference or a validated biological reference.
"""
from typing import List, Sequence


def diffusion_pseudotime(
    features: Sequence[Sequence[float]],
    root_index: int = 0,
    n_neighbors: int = 5,
    n_components: int = 10,
) -> List[float]:
    """Return root-relative spectral diffusion pseudotime scaled to [0, 1].

    Uses a symmetric adaptive Gaussian kNN graph, a row-stochastic diffusion
    operator, and integrated nontrivial eigenmodes weighted by lambda/(1-lambda).
    Dense eigendecomposition is O(n^3); restrict use to <= 300 cells.
    """
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("Install scientific extras: pip install '.[trajectory]'") from exc

    try:
        x = np.asarray(features, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Cell features must be a rectangular numeric matrix") from exc
    if x.ndim != 2 or x.shape[1] == 0 or not 3 <= x.shape[0] <= 300:
        raise ValueError("Expected 3–300 cells and at least one numeric feature")
    if x.shape[1] > 50:
        raise ValueError("At most 50 numeric features are supported")
    if not np.isfinite(x).all():
        raise ValueError("Cell features must be finite")
    n = x.shape[0]
    if not isinstance(root_index, int) or not 0 <= root_index < n:
        raise ValueError("root_index must identify an input cell")
    if not isinstance(n_neighbors, int) or not 2 <= n_neighbors < n:
        raise ValueError("n_neighbors must be between 2 and cell_count - 1")
    if not isinstance(n_components, int) or n_components < 1:
        raise ValueError("n_components must be a positive integer")
    if np.all(x == x[0]):
        raise ValueError("All cells have identical features")

    # Direct differences avoid cancellation in x@x.T.
    d2 = np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2)
    if not np.isfinite(d2).all():
        raise ValueError("Feature scale is too large for stable distance calculation")
    np.fill_diagonal(d2, np.inf)
    neighbors = np.argsort(d2, axis=1, kind="stable")[:, :n_neighbors]
    local_scale = np.sqrt(np.take_along_axis(d2, neighbors, axis=1)[:, -1])
    positive_scales = local_scale[local_scale > 0]
    if positive_scales.size == 0:
        raise ValueError("Cannot infer graph bandwidth from identical cells")
    local_scale = np.where(local_scale > 0, local_scale, positive_scales.min())
    weights = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in neighbors[i]:
            denom = local_scale[i] * local_scale[j]
            weight = float(np.exp(-d2[i, j] / denom)) if denom > 0 else 0.0
            weights[i, j] = max(weights[i, j], weight)
            weights[j, i] = max(weights[j, i], weight)
    # Self loops make the chain aperiodic and improve numerical stability.
    np.fill_diagonal(weights, 1.0)

    # Disconnected kNN graphs have no globally meaningful pseudotime.
    discovered = {root_index}
    frontier = [root_index]
    while frontier:
        i = frontier.pop()
        for j in np.flatnonzero(weights[i] > 0):
            j = int(j)
            if j not in discovered:
                discovered.add(j)
                frontier.append(j)
    if len(discovered) != n:
        raise ValueError("kNN graph is disconnected; increase n_neighbors")

    degree = weights.sum(axis=1)
    inverse_sqrt = 1.0 / np.sqrt(degree)
    symmetric = (inverse_sqrt[:, None] * weights) * inverse_sqrt[None, :]
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]

    # The stationary eigenmode (lambda=1) carries no trajectory information.
    keep = min(n_components, n - 1)
    lam = eigenvalues[1:1 + keep]
    basis = eigenvectors[:, 1:1 + keep] * inverse_sqrt[:, None]
    # Connected stochastic matrices have nontrivial eigenvalues strictly < 1.
    denominator = np.maximum(1.0 - lam, 1e-12)
    coefficients = lam / denominator
    embedding = basis * coefficients
    raw = np.linalg.norm(embedding - embedding[root_index], axis=1)
    maximum = float(raw.max())
    if not np.isfinite(maximum) or maximum <= 0:
        raise ValueError("Degenerate diffusion geometry; no pseudotime can be estimated")
    return (raw / maximum).tolist()
