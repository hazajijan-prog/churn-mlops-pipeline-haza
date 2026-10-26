"""Integrity check for the trained model. Run:  python -m churn.provenance [outputs]

Checks that modell.joblib is the exact file the train job produced: its SHA-256 must
match model_sha256 in matvarden.json, and in GitHub Actions the model must come from
the commit being built. Exits with code 1 otherwise, so the job stops before the model
is loaded. A pickled model can run arbitrary code when loaded, so it is checked first.

Only uses the standard library, so it also runs in jobs that do not install the project.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

MODEL_FILE = "modell.joblib"
METRICS_FILE = "matvarden.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory: Path) -> list[str]:
    """Returns the problems found. An empty list means the model passed."""
    model_path = directory / MODEL_FILE
    metrics_path = directory / METRICS_FILE

    missing = [path for path in (model_path, metrics_path) if not path.exists()]
    if missing:
        return [f"{path} is missing" for path in missing]

    try:
        metrics = json.loads(metrics_path.read_text())
    except json.JSONDecodeError:
        return [f"{metrics_path} is not valid JSON"]

    problems = []
    expected_hash = metrics.get("model_sha256")
    if expected_hash is None:
        problems.append(f"{metrics_path} has no model_sha256")
    elif sha256_file(model_path) != expected_hash:
        problems.append(f"{model_path} does not match model_sha256 in {metrics_path}")

    # GITHUB_SHA only exists in GitHub Actions. Locally the commit is not checked.
    commit = os.environ.get("GITHUB_SHA")
    if commit and metrics.get("commit") != commit:
        problems.append(
            f"the model was trained on commit {metrics.get('commit')}, but this run builds {commit}"
        )
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    directory = Path(argv[0]) if argv else Path("outputs")

    problems = verify(directory)
    if problems:
        print("ERROR: the model failed the integrity check.")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"OK: {directory / MODEL_FILE} matches {METRICS_FILE}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
