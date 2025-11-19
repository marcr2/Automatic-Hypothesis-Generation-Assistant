# M3 Machine Setup Guide

Main processing machine with 198GB VRAM and 1.7TB storage

## Overview

The M3 machine is the primary computation hub of the distributed AHGA system. It runs the Python application, hosts a local LLM server (vLLM), and stores all data except vector databases.

## Hardware Specs

- **VRAM**: 198GB (for large language models)
- **Storage**: 1.7TB (for data, models, and processing)
- **GPU**: CUDA-capable (required for vLLM)

## Services Running on M3

1. **Python Application** - Main AHGA research processor
2. **vLLM Server** - Local LLM inference (Port 11434)
3. **Data Scraping** - PubMed, Semantic Scholar, preprints
4. **Embedding Generation** - Via Google API

## Installation

### Quick Install

```bash
cd /path/to/AHGA
bash deploy/m3/install_m3.sh
```

The installer will:
- Check Python 3.8+, CUDA drivers, disk space
- Install system dependencies (with sudo prompts)
- Create Python virtual environment
- Install vLLM and all dependencies
- Create directory structure
- Configure environment variables
- Optionally set up systemd services

### Manual Installation

If you prefer manual setup or don't have sudo access:

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
pip install vllm

# 3. Create directories
mkdir -p data/{embeddings,scraped_data,logs,backups}
mkdir -p ~/models ~/workspace/temp

# 4. Copy and configure environment
cp deploy/m3/env.m3.example .env
# Edit .env with your settings

# 5. Install systemd service (optional, requires sudo)
# See deploy/m3/systemd/vllm.service
```

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# Machine profile
MACHINE_PROFILE=m3
EXECUTION_MODE=distributed

# ChromaDB (points to Mystery)
CHROMA_HOST=192.168.1.XXX  # Mystery's IP
CHROMA_PORT=8000

# LLM (local vLLM)
LLM_PROVIDER=local
LLM_API_BASE=http://localhost:11434/v1
LLM_MODEL_NAME=meta-llama/Meta-Llama-3.1-70B-Instruct

# Embeddings (Google API)
EMBEDDINGS_PROVIDER=google
GOOGLE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here

# Optional
NCBI_API_KEY=your_key_here
```

### Model Selection

Recommended models for 198GB VRAM:

| Model | VRAM Usage | Best For |
|-------|------------|----------|
| Llama 3.1 70B Instruct | ~140GB | General purpose, recommended |
| Qwen 2.5 72B Instruct | ~145GB | Strong reasoning |
| Mixtral 8x22B Instruct | ~160GB | Mixture of Experts |
| Llama 3.1 8B Instruct | ~16GB | Testing/development |

Change model in `.env`:
```bash
LLM_MODEL_NAME=meta-llama/Meta-Llama-3.1-70B-Instruct
```

## Starting Services

### Option 1: Using Start Script

```bash
cd /path/to/AHGA
./deploy/m3/start_services.sh
```

This starts vLLM in the background with logging.

### Option 2: Using Systemd (if installed)

```bash
sudo systemctl start vllm
sudo systemctl status vllm
sudo journalctl -u vllm -f
```

### Option 3: Manual Start

```bash
source .venv/bin/activate

python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3.1-70B-Instruct \
  --host 0.0.0.0 \
  --port 11434 \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192
```

## Verification

### 1. Check vLLM Server

```bash
curl http://localhost:11434/v1/models
```

### 2. Test Configuration

```bash
source .venv/bin/activate
python -m src.cli.main config show --profile m3
```

### 3. Test Connectivity to Mystery

```bash
python -m src.cli.main config test-connectivity
```

Should show:
- ✅ ChromaDB is responding (on Mystery)
- ✅ LLM server is responding (local)

### 4. Run Full Test

```bash
python scripts/test_distributed_setup.py
```

## Directory Structure

```
/home/user/AHGA/
├── data/
│   ├── embeddings/          # Generated embeddings (50-100GB)
│   │   └── xrvix_embeddings/
│   │       ├── biorxiv/
│   │       ├── medrxiv/
│   │       ├── pubmed/
│   │       └── semantic_scholar/
│   ├── scraped_data/        # Raw scraped papers (10-50GB)
│   ├── logs/                # Application logs
│   │   ├── vllm.log
│   │   └── paper_processing.log
│   ├── backups/             # Backup files
│   └── vector_db/           # Not used in distributed mode
├── hypothesis_export/       # Generated hypotheses
├── .venv/                   # Python virtual environment
└── .env                     # Environment configuration

/home/user/models/           # LLM models (~140GB)
└── huggingface_cache/       # HF cache

/home/user/workspace/temp/   # Temporary processing files
```

## Usage

### Data Pipeline

```bash
source .venv/bin/activate

# 1. Scrape papers
python -m src.cli.main scrape full \
  --pubmed-keywords "mitochondria,apoptosis" \
  --max-results 1000

# 2. Generate embeddings (automatic during scraping)

# 3. Load to ChromaDB (on Mystery)
python -m src.cli.main embeddings load

# 4. Generate hypotheses
python -m src.cli.main hypothesis generate
```

### Monitoring

```bash
# GPU usage
watch nvidia-smi

# vLLM logs
tail -f data/logs/vllm.log

# System resources
htop

# Network to Mystery
ping MYSTERY_IP
```

## Performance Tuning

### vLLM Optimization

Edit systemd service or start script:

```bash
# Use more GPU memory
--gpu-memory-utilization 0.95

# Longer context
--max-model-len 16384

# Multiple GPUs (if available)
--tensor-parallel-size 2

# Quantization (reduces VRAM)
--quantization awq
```

### Network Optimization

- Use wired connection to Mystery
- Check latency: `ping MYSTERY_IP`
- Monitor bandwidth during heavy queries

## Troubleshooting

### vLLM Won't Start

**Check GPU:**
```bash
nvidia-smi
```

**Check logs:**
```bash
tail -f data/logs/vllm.log
# or
sudo journalctl -u vllm -n 50
```

**Common issues:**
- Out of VRAM: Choose smaller model
- CUDA not available: Install NVIDIA drivers
- Model download failed: Check internet/HF token

### Cannot Connect to Mystery

**Test connection:**
```bash
curl http://MYSTERY_IP:8000/api/v1/heartbeat
```

**Solutions:**
- Verify IP address in `.env`
- Check Mystery's firewall: `sudo ufw status` (on Mystery)
- Ensure ChromaDB is running on Mystery
- Test network: `ping MYSTERY_IP`

### Slow Performance

**GPU bottleneck:**
- Check `nvidia-smi` for utilization
- Reduce `max-model-len` if memory-bound

**Network bottleneck:**
- Check latency to Mystery
- Monitor network usage: `iftop`

**ChromaDB bottleneck:**
- Check Mystery's RAM usage
- Optimize ChromaDB on Mystery

## Maintenance

### Update Dependencies

```bash
source .venv/bin/activate
pip install --upgrade vllm
pip install -r requirements.txt --upgrade
```

### Backup Data

```bash
# Backup embeddings
tar -czf embeddings_backup_$(date +%Y%m%d).tar.gz data/embeddings/

# Backup configs
cp .env .env.backup
cp config/*.json config_backup/
```

### Clean Up

```bash
# Remove old logs
find data/logs/ -name "*.log" -mtime +30 -delete

# Clean temp files
rm -rf ~/workspace/temp/*

# Clean HuggingFace cache (if needed)
rm -rf ~/models/huggingface_cache/*
```

## Advanced Features

### Using Multiple GPUs

If you have multiple GPUs:

```bash
# Set tensor parallelism
export TENSOR_PARALLEL_SIZE=2

# Or in .env
TENSOR_PARALLEL_SIZE=2
```

### Custom Models

To use a different model:

1. Update `.env`:
```bash
LLM_MODEL_NAME=mistralai/Mixtral-8x22B-Instruct-v0.1
```

2. Restart vLLM:
```bash
sudo systemctl restart vllm
# or
./deploy/m3/start_services.sh
```

### Gated Models (Llama, etc.)

For gated HuggingFace models:

1. Get HF token from https://huggingface.co/settings/tokens

2. Add to `.env`:
```bash
HF_TOKEN=your_token_here
```

3. Login once:
```bash
huggingface-cli login
```

## CLI Reference

```bash
# Configuration
python -m src.cli.main --profile m3 config show
python -m src.cli.main config test-connectivity

# Services
python -m src.cli.main service start vllm
python -m src.cli.main service status vllm

# Data pipeline
python -m src.cli.main scrape full
python -m src.cli.main embeddings load
python -m src.cli.main hypothesis generate
```

## Support

- **Deployment Guide**: [../README.md](../README.md)
- **Configuration**: [../../CONFIG_GUIDE.md](../../CONFIG_GUIDE.md)
- **Troubleshooting**: [../../TROUBLESHOOTING.md](../../TROUBLESHOOTING.md)
- **Issue Tracker**: Contact system administrator

---

**M3 Machine** | Main Processing Unit | AHGA Research Processor

