# Use official Python runtime as base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv
RUN uv sync --frozen

# Copy the entire project
COPY . .

# Copy and make entrypoint.sh executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose ports if needed (adjust based on your app)
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]