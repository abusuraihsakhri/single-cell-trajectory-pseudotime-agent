"""Validation of exploratory diffusion-map pseudotime, not biological ground truth."""
import csv
import math
import pytest

from cell_trajectory.pseudotime import diffusion_pseudotime
from cli import main


def test_line_monotonicity_and_root():
    values = diffusion_pseudotime([[float(i), 0.0] for i in range(10)],
                                  root_index=0, n_neighbors=2, n_components=9)
    assert values[0] == pytest.approx(0.0, abs=1e-10)
    assert values[-1] == pytest.approx(1.0, abs=1e-10)
    assert all(a < b for a, b in zip(values, values[1:]))


def test_reversing_root_changes_direction():
    values = diffusion_pseudotime([[float(i)] for i in range(8)],
                                  root_index=7, n_neighbors=2, n_components=7)
    assert values[-1] == pytest.approx(0.0, abs=1e-10)
    assert values[0] == pytest.approx(1.0, abs=1e-10)


@pytest.mark.parametrize("features", [
    [[1], [2]],
    [[1], [2], [math.nan]],
    [[1], [2, 3], [4]],
    [[1], [1], [1]],
])
def test_rejects_invalid_matrices(features):
    with pytest.raises(ValueError):
        diffusion_pseudotime(features, n_neighbors=2)


def test_rejects_invalid_hyperparameters():
    x = [[i] for i in range(6)]
    for kwargs in ({"root_index": 99}, {"n_neighbors": 1}, {"n_neighbors": 6}, {"n_components": 0}):
        with pytest.raises(ValueError):
            diffusion_pseudotime(x, **kwargs)


def test_pseudotime_cli_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cells.csv").write_text(
        "cell_id,x,y\n" + "".join(f"C{i},{i},0\n" for i in range(8)),
        encoding="utf-8"
    )
    assert main(["pseudotime", "-i", "cells.csv", "-o", "out.csv",
                 "--root-cell", "C0", "--neighbors", "2", "--components", "7"]) == 0
    with (tmp_path / "out.csv").open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    assert len(data) == 8
    assert float(data[0]["pseudotime"]) == pytest.approx(0.0, abs=1e-10)
    assert float(data[-1]["pseudotime"]) == pytest.approx(1.0, abs=1e-10)
    assert main(["pseudotime", "-i", "cells.csv", "-o", "cells.csv",
                 "--root-cell", "C0"]) == 1
