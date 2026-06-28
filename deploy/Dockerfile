FROM python:3.12-slim

WORKDIR /app

# No gcc needed - use pre-built wheels only
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY app/ ./app/
COPY ai_model/ ./ai_model/
COPY bigdata/ ./bigdata/

RUN mkdir -p /app/uploads /app/ai_models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
