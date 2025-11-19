# Configuration Guide

## Overview

This system supports two execution modes:
- **Local Mode**: All components (ChromaDB, LLM, embeddings) run on a single machine
- **Distributed Mode**: Components are distributed across multiple machines for better performance and scalability

## Quick Start

### Local Mode (Default)

The system works out of the box in local mode with Google APIs. Simply ensure `config/keys.json` contains your API keys:

```json
{
    "GOOGLE_API_KEY": "your_google_api_key",
    "GEMINI_API_KEY": "your_gemini_api_key",
    "ncbi_api_key": "your_ncbi_api_key"
}
```

### Distributed Mode

Set the execution mode and configure endpoints via environment variables or `config/LLM_config.json`.

## Configuration Files

### 1. config/LLM_config.json

Main configuration file for distributed system setup:

```json
{
  "execution_mode": "local",
  "llm": {
    "provider": "gemini",
    "api_base": "http://localhost:11434/v1",
    "model_name": "llama3",
    "api_key": ""
  },
  "embeddings": {
    "provider": "google",
    "api_base": "http://localhost:8001/v1",
    "model_name": "nomic-embed-text",
    "google_api_key": ""
  },
  "chromadb": {
    "host": "localhost",
    "port": 8000,
    "persist_directory": "./data/vector_db/chroma_db"
  }
}
```

**Field Descriptions:**

- `execution_mode`: `"local"` or `"distributed"`
- `llm.provider`: `"gemini"` (Google API) or `"local"` (OpenAI-compatible endpoint)
- `llm.api_base`: Base URL for local LLM server (e.g., vLLM, TGI, Ollama, LM Studio)
- `llm.model_name`: Model identifier to use
- `embeddings.provider`: `"google"` (Google API) or `"local"` (OpenAI-compatible endpoint)
- `embeddings.api_base`: Base URL for local embeddings server
- `chromadb.host`: ChromaDB server hostname/IP (for distributed mode)
- `chromadb.port`: ChromaDB server port (for distributed mode)

### 2. Environment Variables

Environment variables override `LLM_config.json` settings. Create a `.env` file or set these in your shell:

```bash
# Execution Mode
EXECUTION_MODE=distributed

# ChromaDB Configuration (Machine 2)
CHROMA_HOST=192.168.1.101
CHROMA_PORT=8000

# LLM Configuration (Machine 1)
LLM_PROVIDER=local
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL_NAME=llama3

# Embeddings Configuration
EMBEDDINGS_PROVIDER=local
EMBEDDINGS_API_BASE=http://localhost:8001/v1
EMBEDDINGS_MODEL_NAME=nomic-embed-text

# Google API Keys (if using Google providers)
GOOGLE_API_KEY=your_google_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## Distributed Mode Setup

### Two-Machine Architecture

- **Machine 1 (High GPU/Storage)**: Runs main Python script + LLM server + Embeddings server
- **Machine 2 (High RAM)**: Runs ChromaDB server only

### Machine 2 Setup (ChromaDB Server)

1. Install ChromaDB:
```bash
pip install chromadb
```

2. Start ChromaDB server:
```bash
chroma run --host 0.0.0.0 --port 8000
```

3. Verify server is running:
```bash
curl http://localhost:8000/api/v1/heartbeat
```

### Machine 1 Setup (Main Script + LLM + Embeddings)

#### Option A: Using Ollama

1. Install Ollama from https://ollama.ai

2. Start Ollama server:
```bash
ollama serve
```

3. Pull models:
```bash
ollama pull llama3
ollama pull nomic-embed-text
```

4. Configure in `config/LLM_config.json`:
```json
{
  "execution_mode": "distributed",
  "llm": {
    "provider": "local",
    "api_base": "http://localhost:11434/v1",
    "model_name": "llama3"
  },
  "embeddings": {
    "provider": "local",
    "api_base": "http://localhost:11434/v1",
    "model_name": "nomic-embed-text"
  },
  "chromadb": {
    "host": "192.168.1.101",
    "port": 8000
  }
}
```

#### Option B: Using vLLM

1. Install vLLM:
```bash
pip install vllm
```

2. Start vLLM server:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3-8B \
  --host 0.0.0.0 \
  --port 11434
```

3. Start embeddings server (separate):
```bash
python -m vllm.entrypoints.openai.api_server \
  --model BAAI/bge-large-en-v1.5 \
  --host 0.0.0.0 \
  --port 8001
```

4. Configure in `config/LLM_config.json`:
```json
{
  "execution_mode": "distributed",
  "llm": {
    "provider": "local",
    "api_base": "http://localhost:11434/v1",
    "model_name": "meta-llama/Llama-3-8B"
  },
  "embeddings": {
    "provider": "local",
    "api_base": "http://localhost:8001/v1",
    "model_name": "BAAI/bge-large-en-v1.5"
  },
  "chromadb": {
    "host": "192.168.1.101",
    "port": 8000
  }
}
```

#### Option C: Using LM Studio

1. Download and install LM Studio from https://lmstudio.ai

2. Load your preferred model in LM Studio

3. Go to "Local Server" tab and start the server (default: http://localhost:1234/v1)

4. Configure in `config/LLM_config.json`:
```json
{
  "execution_mode": "distributed",
  "llm": {
    "provider": "local",
    "api_base": "http://localhost:1234/v1",
    "model_name": "your-model-name"
  },
  "embeddings": {
    "provider": "google",
    "google_api_key": "your_google_api_key"
  },
  "chromadb": {
    "host": "192.168.1.101",
    "port": 8000
  }
}
```

## Testing Your Configuration

### 1. Test ChromaDB Connection (Distributed Mode)

```python
from src.core.chromadb_manager import ChromaDBManager

manager = ChromaDBManager()
print("ChromaDB connected successfully!")
```

### 2. Test Embeddings

```python
from src.core.embeddings_client import EmbeddingsClient

client = EmbeddingsClient()
embedding = client.get_embedding("Hello, world!")
print(f"Embedding dimension: {len(embedding)}")
```

### 3. Test LLM

```python
from src.core.llm_client import LLMClient

client = LLMClient()
response = client.generate_content("Say hello in one sentence.")
print(response.text)
```

### 4. Display Current Configuration

```python
from src.core.config_loader import display_configuration

display_configuration()
```

## Troubleshooting

### ChromaDB Connection Issues

**Problem**: Cannot connect to ChromaDB server

**Solutions**:
1. Verify ChromaDB server is running on Machine 2:
   ```bash
   curl http://MACHINE2_IP:8000/api/v1/heartbeat
   ```
2. Check firewall settings allow port 8000
3. Verify `CHROMA_HOST` and `CHROMA_PORT` in configuration

### LLM/Embeddings API Issues

**Problem**: LLM or embeddings requests fail

**Solutions**:
1. Verify local server is running:
   ```bash
   curl http://localhost:11434/v1/models
   ```
2. Check model is loaded in the server
3. Verify `LLM_API_BASE` and `EMBEDDINGS_API_BASE` URLs
4. Check server logs for errors

### Google API Rate Limits

**Problem**: Rate limit exceeded errors

**Solutions**:
1. Switch to local provider for embeddings:
   ```json
   {
     "embeddings": {
       "provider": "local",
       "api_base": "http://localhost:8001/v1"
     }
   }
   ```
2. Adjust rate limiting in scraper configuration
3. Wait for quota to reset (usually hourly/daily)

### Mixed Mode Configuration

You can mix providers! For example:
- Use Google Gemini for LLM (for quality)
- Use local embeddings (for speed/cost)
- Use remote ChromaDB (for scalability)

```json
{
  "execution_mode": "distributed",
  "llm": {
    "provider": "gemini",
    "api_key": "your_gemini_key"
  },
  "embeddings": {
    "provider": "local",
    "api_base": "http://localhost:8001/v1",
    "model_name": "nomic-embed-text"
  },
  "chromadb": {
    "host": "192.168.1.101",
    "port": 8000
  }
}
```

## Configuration Priority

Settings are loaded in this order (later overrides earlier):

1. **Default values** (hardcoded)
2. **config/keys.json** (API keys)
3. **config/LLM_config.json** (main configuration)
4. **Environment variables** (highest priority)

## Best Practices

1. **Start with Local Mode**: Test everything works locally before going distributed
2. **Use Environment Variables for Deployment**: Easier to manage across machines
3. **Keep API Keys Secure**: Never commit keys to version control
4. **Monitor Resources**: Watch GPU/RAM usage on both machines
5. **Test Each Component**: Verify ChromaDB, LLM, and embeddings independently
6. **Use Virtual Environments**: Keep dependencies isolated (`venv` or `conda`)

## Advanced Configuration

### Custom Rate Limiting

Modify rate limiting in scraper configuration files:
- Individual scraper scripts (hardcoded configurations)
- Can be customized per scraper as needed

### Multiple ChromaDB Collections

You can maintain separate collections for different data sources or experiments. The system automatically manages collections.

### Load Balancing

For production deployments, consider:
- Multiple LLM replicas behind a load balancer
- Distributed ChromaDB clusters
- Caching layers for embeddings

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `data/logs/`
3. Verify configuration with `display_configuration()`
4. Check server status and connectivity

