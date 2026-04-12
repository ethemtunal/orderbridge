FROM python:3.13-slim

RUN pip install uv

WORKDIR /app/orderbridge

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "uvicorn", "orderbridge.main:app", "--host", "0.0.0.0", "--port", "8000"]
