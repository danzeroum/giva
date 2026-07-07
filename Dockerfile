# Imagem única para API / worker / scheduler — papel definido pelo comando (ADR-05).
FROM python:3.12-slim AS base
WORKDIR /app
COPY pyproject.toml ./
COPY src/ src/
COPY migrations/ migrations/
COPY alembic.ini ./
COPY dados/ dados/
# src/ precisa existir ANTES do install — build baseado em pyproject empacota o
# código-fonte presente.
RUN pip install --no-cache-dir .
# API:       uvicorn giva.api.app:app --host 0.0.0.0 --port 8000  (ADR-07)
# Worker:    python -m giva.worker   (ADR-03)
# O compose sobrescreve `command:` por serviço; este CMD é só o default da imagem.
CMD ["uvicorn", "giva.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
