# Use an official Python runtime as the base image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the backend code to the working directory
COPY . .

# Install the Python dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Run the FastAPI server using Uvicorn
CMD poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000