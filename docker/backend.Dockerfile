FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --requirement requirements.txt

COPY backend/app ./app
COPY backend/rules ./rules
COPY backend/scripts ./scripts
COPY backend/tests ./tests
COPY backend/pytest.ini ./pytest.ini
COPY seed_data ./seed_data

EXPOSE 8000

# Bind $PORT when the host assigns one, which Render does, otherwise the Compose port.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
