FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY core/api/ ./core/api/
COPY core/runtime/ ./core/runtime/
COPY core/memory/ ./core/memory/
COPY core/tools/ ./core/tools/
COPY core/governance/ ./core/governance/
COPY core/models/ ./core/models/
COPY core/sdk/ ./core/sdk/

# Expose port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "core.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
