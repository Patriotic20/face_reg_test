# Use the official uv image for a fast build
FROM astral-sh/uv:python3.12-bookworm-slim AS builder

# Install system dependencies for OpenCV and Dlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Enable bytecode compilation for performance
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of your code
COPY . .

# Final Stage (Compact image)
FROM python:3.12-slim-bookworm

# Install runtime libraries for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Set Path to use the uv virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Replace 'main.py' with your actual entry script
CMD ["python", "main.py"]