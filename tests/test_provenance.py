"""Integrity check of the trained model before it is used."""

import json

import pytest

from churn import model, provenance

COMMIT = "abc123"


@pytest.fixture(autouse=True)
def no_github_sha(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)


@pytest.fixture
def outputs(tmp_path):
    model_path = tmp_path / "modell.joblib"
    model_path.write_bytes(b"trained model")
    metrics = {"roc_auc": 0.8, "commit": COMMIT, "model_sha256": provenance.sha256_file(model_path)}
    (tmp_path / "matvarden.json").write_text(json.dumps(metrics))
    return tmp_path


def write_metrics(directory, **changes):
    path = directory / "matvarden.json"
    metrics = json.loads(path.read_text()) | changes
    path.write_text(json.dumps(metrics))


def test_untouched_model_passes(outputs):
    assert provenance.verify(outputs) == []
    assert provenance.main([str(outputs)]) == 0


def test_swapped_model_is_stopped(outputs):
    (outputs / "modell.joblib").write_bytes(b"another model")
    problems = provenance.verify(outputs)
    assert len(problems) == 1
    assert "does not match model_sha256" in problems[0]
    assert provenance.main([str(outputs)]) == 1


def test_missing_hash_is_stopped(outputs):
    path = outputs / "matvarden.json"
    metrics = json.loads(path.read_text())
    del metrics["model_sha256"]
    path.write_text(json.dumps(metrics))
    assert provenance.verify(outputs) == [f"{path} has no model_sha256"]


@pytest.mark.parametrize("filename", ["modell.joblib", "matvarden.json"])
def test_missing_file_is_stopped(outputs, filename):
    (outputs / filename).unlink()
    assert provenance.verify(outputs) == [f"{outputs / filename} is missing"]


def test_invalid_metrics_file_is_stopped(outputs):
    (outputs / "matvarden.json").write_text("{not json")
    assert provenance.verify(outputs) == [f"{outputs / 'matvarden.json'} is not valid JSON"]


def test_model_from_another_commit_is_stopped(outputs, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "def456")
    problems = provenance.verify(outputs)
    assert len(problems) == 1
    assert "trained on commit abc123" in problems[0]


def test_model_from_the_same_commit_passes(outputs, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", COMMIT)
    assert provenance.verify(outputs) == []


def test_edited_metrics_are_not_caught_by_the_hash(outputs):
    # The hash only covers the model file. Edited metrics are caught by the signed
    # attestation in CI, which is why the pipeline uses both.
    write_metrics(outputs, roc_auc=0.99)
    assert provenance.verify(outputs) == []


def test_trained_model_passes_the_check(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_RUN_ID", "42")
    model.main(tmp_path)
    metrics = json.loads((tmp_path / "matvarden.json").read_text())
    assert metrics["model_sha256"] == provenance.sha256_file(tmp_path / "modell.joblib")
    assert metrics["run_id"] == "42"
    assert provenance.verify(tmp_path) == []
