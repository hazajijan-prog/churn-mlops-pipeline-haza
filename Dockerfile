FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .

# Installera runtime-beroenden innan koden kopieras.
RUN python - <<'PY'
import subprocess
import sys
import tomllib

with open("pyproject.toml", "rb") as f:
    dependencies = tomllib.load(f)["project"]["dependencies"]

subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "--no-cache-dir", *dependencies]
)
PY

COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

COPY data/ ./data/

RUN useradd --create-home appuser \
    && mkdir -p /app/outputs \
    && chown -R appuser:appuser /app/outputs

COPY outputs/modell.joblib ./outputs/modell.joblib

USER appuser

CMD ["python", "-m", "churn.score"]