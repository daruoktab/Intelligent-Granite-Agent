# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory in container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web_app.py
ENV FLASK_ENV=production
ENV OLLAMA_HOST=0.0.0.0:11434

# Install system dependencies including Ollama
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Create ollama user and directories
RUN useradd -r -s /bin/false -m -d /usr/share/ollama ollama

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a startup script
RUN echo '#!/bin/bash\n\
# Start Ollama server in background\n\
ollama serve &\n\
\n\
# Wait for Ollama to be ready\n\
echo "Waiting for Ollama to start..."\n\
sleep 10\n\
\n\
# Pull the required model (granite3.3 ~4.9GB download)\n\
echo "Downloading granite3.3 model (~4.9GB)..."\n\
echo "Note: This will be slower on CPU-only systems"\n\
ollama pull granite3.3\n\
\n\
# Start the Flask application\n\
echo "Starting Flask application..."\n\
python web_app.py' > /app/start.sh && chmod +x /app/start.sh

# Create a non-root user for security (but ollama needs to run as root initially)
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chmod +x /app/start.sh

# Expose the ports (Flask app and Ollama)
EXPOSE 12000 11434

# Health check for both services
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:12000/ && curl -f http://localhost:11434/api/tags || exit 1

# Command to run both Ollama and the application
CMD ["/app/start.sh"]


