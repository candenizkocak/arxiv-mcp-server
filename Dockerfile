# Generated by https://smithery.ai. See: https://smithery.ai/docs/build/project-config
FROM python:3.13-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock arxiv_server.py ./

# Install dependencies
RUN pip install --no-cache-dir .

# Set entrypoint for stdio transport
ENTRYPOINT ["python", "arxiv_server.py"]
