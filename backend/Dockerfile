# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

RUN apt-get update && apt-get install -y curl

RUN pip install uv

COPY pyproject.toml uv.lock ./
COPY data ./data

RUN uv sync

COPY mm_ai ./mm_ai

ARG FRONTEND_PORT
ENV FRONTEND_PORT=${FRONTEND_PORT}

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "uvicorn", "mm_ai.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
