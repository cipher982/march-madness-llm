# Use an official Python runtime as the base image
FROM python:3.12

RUN apt-get update && apt-get install -y curl

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the backend code to the working directory
COPY . .

# Install the Python dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

ARG FRONTEND_PORT
ENV FRONTEND_PORT=${FRONTEND_PORT}

# Set the working directory and run the FastAPI server using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
