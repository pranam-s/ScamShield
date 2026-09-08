"""Lightweight tests for src/train.py helpers (no model download / training)."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

import train


def test_compute_metrics_perfect_predictions(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMetric:
        def compute(self, predictions, references):
            correct = sum(int(p == r) for p, r in zip(predictions, references, strict=True))
            return {"accuracy": correct / len(references)}

    monkeypatch.setattr(train, "_accuracy_metric", lambda: FakeMetric())
    p = SimpleNamespace(
        predictions=np.array([[0.9, 0.1], [0.2, 0.8], [0.7, 0.3]]),
        label_ids=np.array([0, 1, 1]),
    )
    result = train.compute_metrics(p)
    assert result == {"accuracy": pytest.approx(2 / 3)}


def test_eval_split_fraction_sane() -> None:
    assert 0.0 < train.EVAL_SPLIT_FRACTION < 1.0
