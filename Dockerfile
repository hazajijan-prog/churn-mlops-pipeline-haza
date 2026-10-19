FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ ./src/
COPY data/ ./data/

RUN pip install --no-cache-dir -e .

RUN useradd --create-home appuser \
    && mkdir -p /app/outputs \
    && chown -R appuser:appuser /app/outputs

COPY outputs/modell.joblib ./outputs/modell.joblib

USER appuser

CMD [ "python","-m","churn.score" ]