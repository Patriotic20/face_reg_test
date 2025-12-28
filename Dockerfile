# Use a standard Python image
FROM python:3.12-slim-bookworm

# Install UV inside the container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies for DeepFace (OpenCV, TF, and build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
# Note: You MUST have a pyproject.toml or requirements.txt
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen

# Copy your code
COPY . .

# Use the virtual environment path
ENV PATH="/app/.venv/bin:$PATH"

# Run your app (ensure main.py is your entry point)
CMD ["python", "main.py"]