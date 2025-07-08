# Use an official Python runtime as a parent image
# Version: 1.1
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV PORT 8080

# Run app.py when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app.main:app"] 
