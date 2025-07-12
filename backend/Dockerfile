# Backend Dockerfile for MCP Trading Agent
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    automake \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib
RUN curl -L https://downloads.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz -o ta-lib-0.4.0-src.tar.gz && \
    tar -zxvf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    cp $(automake --print-libdir)/config.guess . && \
    cp $(automake --print-libdir)/config.sub . && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    ln -s /usr/lib/libta_lib.so /usr/lib/libta-lib.so && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install FastMCP
RUN pip install fastmcp

# Copy application code
COPY mcp_trading_agent/ ./mcp_trading_agent/
COPY backend/main.py .

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]