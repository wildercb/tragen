# External GPU Server Setup Guide
==========================================

This guide explains how to set up and configure external GPU servers for the NQ Trading Agent to enable high-performance LLM inference.

## Overview

The MCP Trading Agent supports connecting to external GPU servers for enhanced AI analysis capabilities. This allows you to:

- Use powerful GPU hardware for large language models
- Scale compute resources independently
- Support multiple GPU endpoints with automatic failover
- Switch between local and cloud-based inference

## Configuration

### 1. Enable External GPU Provider

Edit `mcp_trading_agent/config/config.yaml`:

```yaml
llm:
  providers:
    external_gpu:
      enabled: true
      endpoints:
        - name: "local_gpu_server"
          url: "http://localhost:8002/v1"
          api_key: "${GPU_SERVER_API_KEY}"
          models: ["llama3-70b", "mixtral-8x7b"]
        - name: "cloud_gpu"
          url: "https://api.your-gpu-provider.com/v1"
          api_key: "${CLOUD_GPU_API_KEY}"
          models: ["llama3-405b", "gpt-4-turbo"]
```

### 2. Set Environment Variables

```bash
export GPU_SERVER_API_KEY="your-local-gpu-server-key"
export CLOUD_GPU_API_KEY="your-cloud-gpu-provider-key"
```

## GPU Server Setup Options

### Option 1: Local GPU Server with Ollama

1. **Install Ollama on GPU Machine:**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama with API Access:**
   ```bash
   OLLAMA_HOST=0.0.0.0:11434 ollama serve
   ```

3. **Pull Models:**
   ```bash
   ollama pull llama3:70b
   ollama pull mixtral:8x7b
   ```

4. **Configure in Trading Agent:**
   ```yaml
   external_gpu:
     enabled: true
     endpoints:
       - name: "local_ollama"
         url: "http://GPU_SERVER_IP:11434/v1"
         models: ["llama3:70b", "mixtral:8x7b"]
   ```

### Option 2: vLLM Server

1. **Install vLLM:**
   ```bash
   pip install vllm
   ```

2. **Start vLLM Server:**
   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model meta-llama/Llama-3-70b-chat-hf \
     --host 0.0.0.0 \
     --port 8001
   ```

3. **Configure in Trading Agent:**
   ```yaml
   external_gpu:
     enabled: true
     endpoints:
       - name: "vllm_server"
         url: "http://GPU_SERVER_IP:8001/v1"
         models: ["meta-llama/Llama-3-70b-chat-hf"]
   ```

### Option 3: Cloud GPU Providers

#### RunPod

1. **Deploy RunPod Instance:**
   - Use RunPod's vLLM template
   - Select your desired model
   - Note the endpoint URL and API key

2. **Configure:**
   ```yaml
   external_gpu:
     enabled: true
     endpoints:
       - name: "runpod"
         url: "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
         api_key: "${RUNPOD_API_KEY}"
         models: ["llama3-70b"]
   ```

#### Together AI

```yaml
external_gpu:
  enabled: true
  endpoints:
    - name: "together"
      url: "https://api.together.xyz/v1"
      api_key: "${TOGETHER_API_KEY}"
      models: ["meta-llama/Llama-3-70b-chat-hf"]
```

## API Usage

### 1. Check Provider Status

```bash
curl http://localhost:8001/api/providers/status
```

### 2. List Available Models

```bash
curl http://localhost:8001/api/providers/models
```

### 3. Switch to External GPU

```bash
curl -X POST "http://localhost:8001/api/providers/switch-model" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "external_gpu",
    "model": "llama3-70b"
  }'
```

### 4. Add New GPU Endpoint

```bash
curl -X POST "http://localhost:8001/api/providers/external-gpu/add" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_gpu_server",
    "url": "http://new-server:8001/v1",
    "api_key": "your-api-key",
    "models": ["llama3-405b"]
  }'
```

## Agent Configuration

### Configure Agents to Use External GPU

```yaml
agents:
  analysis_agent:
    provider: "external_gpu"
    model: "llama3-70b"
    temperature: 0.1
    max_tokens: 2000
```

### Switch Agent Model via API

```bash
curl -X POST "http://localhost:8001/api/providers/switch-model" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "external_gpu",
    "model": "llama3-70b",
    "agent_id": "analysis_20250711_123456"
  }'
```

## Load Balancing and Failover

The system automatically handles:

- **Health Monitoring:** Endpoints are checked regularly
- **Automatic Failover:** If one endpoint fails, traffic routes to healthy ones
- **Load Distribution:** Requests are distributed across available endpoints

## Performance Optimization

### 1. Model Selection by Task

```yaml
agents:
  analysis_agent:
    provider: "external_gpu"
    model: "llama3-70b"  # Large model for complex analysis
    
  execution_agent:
    provider: "ollama"
    model: "phi3:mini"   # Fast local model for quick decisions
    
  risk_agent:
    provider: "external_gpu"  
    model: "mixtral-8x7b"     # Reasoning model for risk assessment
```

### 2. Endpoint Prioritization

Configure endpoints in order of preference:

```yaml
external_gpu:
  enabled: true
  endpoints:
    # Fastest/cheapest first
    - name: "local_gpu"
      url: "http://localhost:8001/v1"
      models: ["llama3-70b"]
    # Cloud backup
    - name: "cloud_gpu"
      url: "https://api.cloud-provider.com/v1"
      api_key: "${CLOUD_API_KEY}"
      models: ["llama3-70b"]
```

## Monitoring

### Health Checks

Monitor endpoint health:

```bash
# Check overall status
curl http://localhost:8001/api/providers/status

# Check specific endpoint
curl http://YOUR_GPU_SERVER:8001/health
```

### Logs

Monitor GPU usage in logs:

```bash
docker-compose logs backend | grep "external_gpu"
```

## Security Considerations

1. **API Keys:** Store securely in environment variables
2. **Network:** Use VPNs or private networks for GPU servers
3. **HTTPS:** Always use HTTPS for cloud endpoints
4. **Authentication:** Implement proper authentication on GPU servers

## Troubleshooting

### Common Issues

1. **Connection Timeout:**
   ```
   # Increase timeout in config
   external_gpu:
     timeout_seconds: 300
   ```

2. **Model Not Found:**
   ```bash
   # Check available models on server
   curl http://GPU_SERVER:8001/v1/models
   ```

3. **Authentication Failed:**
   ```bash
   # Verify API key
   curl -H "Authorization: Bearer $API_KEY" \
        http://GPU_SERVER:8001/v1/models
   ```

4. **Performance Issues:**
   - Check GPU memory usage
   - Monitor network latency
   - Verify model quantization settings

### Debug Commands

```bash
# Test direct connection
curl -X POST "http://GPU_SERVER:8001/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "llama3-70b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Check backend logs
docker-compose logs backend | tail -f
```

## Best Practices

1. **Redundancy:** Configure multiple endpoints for reliability
2. **Model Selection:** Match model capabilities to task requirements
3. **Cost Optimization:** Use local models for frequent, simple tasks
4. **Monitoring:** Set up alerts for endpoint failures
5. **Scaling:** Add more endpoints as trading volume increases

For more information, see the main documentation and API reference.