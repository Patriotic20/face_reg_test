# Use official Python runtime as base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python -m venv .venv

# Install uv in the virtual environment
RUN .venv/bin/pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv
RUN .venv/bin/uv sync

# Copy the entire project
COPY . .

# Copy and make entrypoint.sh executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Expose ports if needed (adjust based on your app)
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]