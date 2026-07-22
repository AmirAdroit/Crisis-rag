FROM python:3.11-slim

WORKDIR /code

# Pre-cache HF models into the image layer's cache dir at runtime via volume.
ENV HF_HOME=/code/.hf_cache

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "httpx<0.28"

COPY app ./app
COPY scripts ./scripts
COPY configs ./configs
COPY data ./data

EXPOSE 8080
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
