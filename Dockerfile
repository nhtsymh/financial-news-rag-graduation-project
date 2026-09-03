FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FNRAG_DATA_DIR=/app/runtime_data \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[infra]"

COPY app.py ./
COPY data ./data
RUN mkdir -p /app/runtime_data && chown -R appuser:appuser /app

USER appuser
EXPOSE 7860
CMD ["python", "app.py"]
