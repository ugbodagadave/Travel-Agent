# Use an official Python runtime as a parent image
# Version: 1.3-worker
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Run the Celery worker
CMD ["celery", "-A", "app.celery_worker.celery_app", "worker", "--loglevel=info"] 