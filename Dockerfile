# Level 1: builder
# Install dependencies in a different layer so they don't affect  the final image
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy only the requirements first — Docker caches this layer if requirements haven't changed
COPY requirements.txt .

# Install dependencies in a different folder so we can copy them into the runtime image
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# Level 2: runtime
# New slim image — no build tools or cache, just what needed to run
FROM python:3.12-slim

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Run the app
# app.main:app means: app folder -> main.py file -> app variable
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
