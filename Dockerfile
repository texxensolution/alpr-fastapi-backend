# Use the official Python image as a base
FROM python:3.12-slim

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1  # Prevents Python from writing pyc files
# ENV PYTHONUNBUFFERED 1  # Ensures stdout and stderr streams are unbuffered

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code into the container
COPY . .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the FastAPI application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
