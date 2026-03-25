FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create logs directory and external_cogs directory for hot-swappable plugins
RUN mkdir -p logs external_cogs

# Mount point for hot-swappable external Cogs
# Docker Compose example:
#   volumes:
#     - ./my_plugins:/app/external_cogs
VOLUME /app/external_cogs

# Run bot
CMD ["uv", "run", "python", "main.py"]
