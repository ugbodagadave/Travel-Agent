# worker.Dockerfile
# Use an official Python runtime as a parent image
# Version: 1.3
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install supervisor
RUN apt-get update && apt-get install -y supervisor

# Copy the rest of the application's code into the container
COPY . .

# Copy the supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# This Dockerfile is for the Celery worker.
# It does NOT expose a port, so Cloud Run will not create a health check.

# Define environment variable
ENV PORT 8080

# Run supervisord
CMD ["/usr/bin/supervisord"] 