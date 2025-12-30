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

# Create logs directory
RUN mkdir -p logs

# Run bot
CMD ["uv", "run", "python", "main.py"]
