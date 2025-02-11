# Use the official Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Install uv and other dependencies
RUN pip install uv && uv pip install --system pyproject.toml
# Install uvicorn directly
RUN pip install uvicorn
# Expose the application port
EXPOSE 8000

# Start the FastAPI application using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]