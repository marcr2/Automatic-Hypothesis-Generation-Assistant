# Distributed Deployment Guide

## Overview

This directory contains machine-specific configurations and scripts for deploying the AHGA Research Processor in a distributed architecture across two machines.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Distributed Architecture                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐         ┌──────────────────────────┐
│    M3 Machine            │         │   Mystery Machine        │
│  (Main Processing)       │         │   (Vector Database)      │
├──────────────────────────┤         ├──────────────────────────┤
│ Resources:               │         │ Resources:               │
│ - 198GB VRAM             │         │ - 100GB+ RAM             │
│ - 1.7TB Storage          │         │ - Storage for vectors    │
│                          │         │                          │
│ Services:                │         │ Services:                │
│ - Python Application     │◄────────┤ - ChromaDB Server        │
│ - vLLM (70B model)       │  8000   │   (Port 8000)            │
│ - Google Embeddings API  │         │                          │
│                          │         │                          │
│ Data Storage:            │         │ Data Storage:            │
│ - Embeddings (JSON)      │         │ - Vector DB only         │
│ - Scraped papers         │         │                          │
│ - Logs & exports         │         │                          │
│ - Models                 │         │                          │
└──────────────────────────┘         └──────────────────────────┘
```

## Machine Roles

### M3 Machine - Main Processing
- **Purpose**: Primary computation, data processing, LLM inference
- **Runs**: Python application, vLLM server, scraping, embedding generation
- **Stores**: Embeddings, scraped data, models, logs, hypothesis exports
- **Port**: 11434 (vLLM API)

### Mystery Machine - Vector Database
- **Purpose**: Vector storage and similarity search
- **Runs**: ChromaDB server only
- **Stores**: Vector database (ChromaDB)
- **Port**: 8000 (ChromaDB API)

## Data Allocation Strategy

### M3 Machine (1.7TB storage)
```
/home/user/AHGA/
├── data/
│   ├── embeddings/          ~50-100GB (JSON files)
│   ├── scraped_data/        ~10-50GB (raw papers)
│   ├── logs/                ~1-5GB
│   ├── backups/             ~50GB
│   └── hypothesis_export/   ~1-10GB
│
/home/user/models/           ~140GB (LLM models)
/home/user/workspace/temp/   ~100GB (temp processing)
```

### Mystery Machine (100GB+ RAM)
```
/home/user/chromadb_data/    Variable (vector database)
/home/user/chromadb_logs/    ~1GB (logs)
```

**Rationale**:
- ChromaDB vectors benefit from RAM (Mystery has 100GB+)
- Embeddings stay on M3 for faster local access during generation
- LLM models on M3 (requires GPU access)
- Temp files on M3 (processing happens there)

## Quick Start

### Step 1: Install Mystery Machine (ChromaDB Server)

```bash
# On Mystery machine
cd /path/to/AHGA
bash deploy/mystery/install_mystery.sh

# Note the IP address shown at the end
# Example: 192.168.1.100
```

### Step 2: Install M3 Machine (Main Application)

```bash
# On M3 machine
cd /path/to/AHGA
bash deploy/m3/install_m3.sh

# When prompted, enter Mystery machine's IP address
```

### Step 3: Start Services

```bash
# On Mystery machine - Start ChromaDB
./deploy/mystery/start_services.sh
# OR if installed as systemd service:
sudo systemctl start chromadb

# On M3 machine - Start vLLM
./deploy/m3/start_services.sh
# OR if installed as systemd service:
sudo systemctl start vllm
```

### Step 4: Verify Setup

```bash
# On M3 machine
source .venv/bin/activate
python -m src.cli.main config show --profile m3
python -m src.cli.main config test-connectivity
python scripts/test_distributed_setup.py
```

## Machine Profiles

Machine profiles automatically configure the system for each machine's role.

### Available Profiles

- `m3`: Main processing machine configuration
- `mystery`: ChromaDB server configuration
- `auto`: Auto-detect based on hostname or running services
- `none`: No profile (use default/manual config)

### Using Profiles

```bash
# Explicit profile
python -m src.cli.main --profile m3 config show

# Auto-detection
python -m src.cli.main --profile auto config show

# Set via environment variable
export MACHINE_PROFILE=m3
python -m src.cli.main config show
```

### Profile Auto-Detection

The system auto-detects profiles based on:
1. `MACHINE_PROFILE` environment variable
2. Hostname (contains "m3" or "mystery")
3. Running services (vLLM on M3, ChromaDB on Mystery)

## Configuration Files

### M3 Configuration
- **Profile**: `deploy/m3/config_m3.json`
- **Environment**: `deploy/m3/env.m3.example` (copy to `.env`)
- **Systemd**: `deploy/m3/systemd/vllm.service`

### Mystery Configuration
- **Profile**: `deploy/mystery/config_mystery.json`
- **Environment**: `deploy/mystery/env.mystery.example`
- **Systemd**: `deploy/mystery/systemd/chromadb.service`

## Network Configuration

### Firewall Rules

**On Mystery Machine:**
```bash
# Allow ChromaDB port
sudo ufw allow 8000/tcp

# Check status
sudo ufw status
```

**On M3 Machine:**
```bash
# Test connection to Mystery
curl http://MYSTERY_IP:8000/api/v1/heartbeat
```

### Connectivity Requirements

- M3 must be able to connect to Mystery on port 8000
- Both machines should be on the same network (recommended)
- Low latency connection preferred for performance

## Service Management

### Using Systemd (Recommended)

```bash
# M3 Machine
sudo systemctl start vllm
sudo systemctl stop vllm
sudo systemctl restart vllm
sudo systemctl status vllm
sudo journalctl -u vllm -f

# Mystery Machine
sudo systemctl start chromadb
sudo systemctl stop chromadb
sudo systemctl restart chromadb
sudo systemctl status chromadb
sudo journalctl -u chromadb -f
```

### Manual Start (Alternative)

```bash
# M3 Machine
cd /path/to/AHGA
./deploy/m3/start_services.sh

# Mystery Machine
cd /path/to/AHGA (or wherever installed)
./deploy/mystery/start_services.sh
```

## Monitoring

### M3 Machine

```bash
# GPU usage
watch nvidia-smi

# vLLM logs
tail -f data/logs/vllm.log

# System resources
htop
```

### Mystery Machine

```bash
# RAM usage
watch free -h

# ChromaDB logs
tail -f ~/chromadb_logs/chromadb.log

# System resources
htop
```

## Troubleshooting

### Cannot Connect to ChromaDB

**Symptoms**: M3 cannot reach ChromaDB on Mystery

**Solutions**:
1. Verify ChromaDB is running: `curl http://localhost:8000/api/v1/heartbeat` (on Mystery)
2. Check firewall: `sudo ufw status` (on Mystery)
3. Verify IP address in M3's `.env` file
4. Test network connectivity: `ping MYSTERY_IP` (from M3)

### vLLM Out of Memory

**Symptoms**: vLLM fails to load model

**Solutions**:
1. Choose smaller model or reduce `GPU_MEMORY_UTILIZATION`
2. Check GPU memory: `nvidia-smi`
3. Ensure no other processes using GPU

### ChromaDB Performance Issues

**Symptoms**: Slow similarity searches

**Solutions**:
1. Ensure sufficient RAM available
2. Check disk I/O if data doesn't fit in RAM
3. Consider SSD for ChromaDB data directory

### Connection Timeout

**Symptoms**: M3 times out connecting to Mystery

**Solutions**:
1. Verify network stability
2. Check if ChromaDB is under heavy load
3. Increase timeout values in configuration

## Data Management

### Backup ChromaDB

```bash
# From Mystery machine
cd ~/chromadb_data
tar -czf chromadb_backup_$(date +%Y%m%d).tar.gz ./*

# Copy to M3 for safe storage
rsync -avz chromadb_backup_*.tar.gz user@M3_IP:/home/user/AHGA/data/backups/
```

### Sync Embeddings (if needed)

```bash
# From M3 to Mystery (if processing locally on Mystery)
rsync -avz --progress data/embeddings/ user@MYSTERY_IP:/home/user/embeddings/
```

## Performance Tuning

### M3 Machine

**vLLM Optimization:**
- Adjust `GPU_MEMORY_UTILIZATION` (0.8-0.95)
- Use tensor parallelism for multiple GPUs
- Increase `MAX_MODEL_LEN` for longer contexts

**Network:**
- Use wired connection over WiFi
- Consider 10GbE if available

### Mystery Machine

**ChromaDB Optimization:**
- Ensure data fits in RAM for best performance
- Use SSD storage if data exceeds RAM
- Monitor memory usage and swap

## Security Considerations

1. **Firewall**: Only open necessary ports (8000 for ChromaDB)
2. **Network**: Use private network or VPN
3. **API Keys**: Store in `.env` files, never commit
4. **Access Control**: Limit SSH access to both machines
5. **Updates**: Keep systems and dependencies updated

## Documentation

- **M3 Setup**: [README_M3.md](m3/README_M3.md)
- **Mystery Setup**: [README_MYSTERY.md](mystery/README_MYSTERY.md)
- **Configuration**: [CONFIG_GUIDE.md](../CONFIG_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)

## Support

For issues or questions:
1. Check machine-specific README files
2. Review logs on each machine
3. Test connectivity: `python -m src.cli.main config test-connectivity`
4. Run diagnostic script: `python scripts/test_distributed_setup.py`

---

**Last Updated**: November 2025

