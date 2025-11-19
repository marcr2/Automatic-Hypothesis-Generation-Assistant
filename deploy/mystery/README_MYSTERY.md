# Mystery Machine Setup Guide

RAM-heavy machine with 100GB+ RAM for ChromaDB vector database

## Overview

The Mystery machine serves as the dedicated vector database server for the distributed AHGA system. It runs only ChromaDB, optimized for high-RAM environments.

## Hardware Specs

- **RAM**: 100GB+ (for vector storage in memory)
- **Storage**: 50GB+ recommended for ChromaDB persistence
- **Network**: Stable connection to M3 machine

## Services Running on Mystery

1. **ChromaDB Server** - Vector database (default port: 8000, configurable)

## Installation

### Quick Install

```bash
cd /path/to/AHGA  # or any directory
bash deploy/mystery/install_mystery.sh
```

The installer will:
- Check Python 3.8+, RAM, disk space
- Install system dependencies (with sudo prompts if available)
- Create Python virtual environment
- Install ChromaDB
- Create directory structure
- Configure firewall (optional)
- Set up systemd service (optional)
- Start ChromaDB server

### Manual Installation

If you prefer manual setup:

```bash
# 1. Create virtual environment
python3 -m venv ~/chromadb_venv
source ~/chromadb_venv/bin/activate

# 2. Install ChromaDB
pip install chromadb

# 3. Create directories
mkdir -p ~/chromadb_data ~/chromadb_logs

# 4. Configure firewall (if needed)
sudo ufw allow 8000/tcp

# 5. Start ChromaDB
chroma run --host 0.0.0.0 --port 8000 --path ~/chromadb_data
```

## Configuration

### Port Configuration

ChromaDB port is configurable during installation or via environment variable:

```bash
# Set custom port
export CHROMA_PORT=8001

# Or in systemd service file
Environment="CHROMA_PORT=8001"
```

### Firewall Configuration

Ensure M3 machine can connect:

```bash
# Allow ChromaDB port (change 8000 to your port)
sudo ufw allow 8000/tcp
sudo ufw status
```

### Network Information

After installation, note your IP address:

```bash
hostname -I
# Example output: 192.168.1.100
```

Provide this IP to M3 machine during its installation.

## Starting Services

### Option 1: Using Start Script

```bash
# Set port if not default
export CHROMA_PORT=8000
./deploy/mystery/start_services.sh
```

### Option 2: Using Systemd (if installed)

```bash
sudo systemctl start chromadb
sudo systemctl status chromadb
sudo journalctl -u chromadb -f
```

### Option 3: Manual Start

```bash
source ~/chromadb_venv/bin/activate
chroma run --host 0.0.0.0 --port 8000 --path ~/chromadb_data
```

## Verification

### 1. Test ChromaDB Server

```bash
curl http://localhost:8000/api/v1/heartbeat
```

Should return heartbeat response.

### 2. Test from M3 Machine

From M3:
```bash
curl http://MYSTERY_IP:8000/api/v1/heartbeat
```

### 3. Check Running Process

```bash
ps aux | grep chroma
```

## Directory Structure

```
/home/user/
├── chromadb_venv/          # Python virtual environment
├── chromadb_data/          # ChromaDB vector storage (grows with data)
└── chromadb_logs/          # Log files
    ├── chromadb.log
    └── chromadb_error.log
```

## Monitoring

### RAM Usage

```bash
# Monitor RAM in real-time
watch free -h

# Or with htop
htop
```

ChromaDB benefits from high RAM as it can keep vectors in memory for faster searches.

### ChromaDB Logs

```bash
# Tail logs
tail -f ~/chromadb_logs/chromadb.log

# Or systemd logs
sudo journalctl -u chromadb -f
```

### Network Connections

```bash
# See incoming connections
sudo netstat -tulpn | grep :8000

# Or with ss
ss -tulpn | grep :8000
```

## Performance

### RAM Optimization

ChromaDB performs best when data fits in RAM:

- **Monitor RAM usage**: `free -h`
- **Check swap usage**: `swapon --show`
- **Avoid swapping**: Ensure RAM > database size

### Storage Optimization

If data exceeds RAM:

- **Use SSD**: Faster disk I/O
- **Monitor disk usage**: `df -h`
- **Check disk I/O**: `iotop`

## Troubleshooting

### ChromaDB Won't Start

**Check logs:**
```bash
tail -f ~/chromadb_logs/chromadb.log
# or
sudo journalctl -u chromadb -n 50
```

**Common issues:**
- Port already in use: Change port
- Permission denied: Check directory permissions
- Python import errors: Reinstall ChromaDB

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8000

# Change to different port
export CHROMA_PORT=8001
./deploy/mystery/start_services.sh
```

### M3 Cannot Connect

**Verify ChromaDB is running:**
```bash
curl http://localhost:8000/api/v1/heartbeat
```

**Check firewall:**
```bash
sudo ufw status
# If port is blocked, allow it
sudo ufw allow 8000/tcp
```

**Check IP address:**
```bash
ip addr show
# or
hostname -I
```

**Test from M3:**
```bash
# On M3 machine
ping MYSTERY_IP
curl http://MYSTERY_IP:8000/api/v1/heartbeat
```

### Out of Memory

**Check RAM usage:**
```bash
free -h
```

**Solutions:**
- Clear old collections
- Restart ChromaDB
- Add more RAM
- Move to SSD storage

## Maintenance

### Restart Service

```bash
# Systemd
sudo systemctl restart chromadb

# Manual
pkill -f "chroma run"
./deploy/mystery/start_services.sh
```

### Backup ChromaDB Data

```bash
# Stop ChromaDB first
sudo systemctl stop chromadb

# Backup
cd ~/chromadb_data
tar -czf ~/chromadb_backup_$(date +%Y%m%d).tar.gz ./*

# Copy to M3 for safe storage
rsync -avz ~/chromadb_backup_*.tar.gz user@M3_IP:/home/user/AHGA/data/backups/

# Restart ChromaDB
sudo systemctl start chromadb
```

### Restore from Backup

```bash
# Stop ChromaDB
sudo systemctl stop chromadb

# Restore
cd ~/chromadb_data
tar -xzf ~/chromadb_backup_YYYYMMDD.tar.gz

# Restart
sudo systemctl start chromadb
```

### Update ChromaDB

```bash
source ~/chromadb_venv/bin/activate
pip install --upgrade chromadb

# Restart service
sudo systemctl restart chromadb
```

### Clean Old Logs

```bash
# Remove logs older than 30 days
find ~/chromadb_logs/ -name "*.log" -mtime +30 -delete
```

## Security

### Network Security

- **Firewall**: Only allow M3's IP if possible
- **Private Network**: Keep Mystery on private network
- **VPN**: Use VPN for remote access

Example specific IP allow:
```bash
sudo ufw allow from M3_IP to any port 8000
```

### Access Control

- **SSH**: Disable password auth, use keys only
- **Updates**: Keep system updated
- **Monitoring**: Monitor for unusual activity

## System Service Management

### Enable Auto-Start

```bash
sudo systemctl enable chromadb
```

### Disable Auto-Start

```bash
sudo systemctl disable chromadb
```

### Service Status

```bash
systemctl status chromadb
```

### Service Logs

```bash
# Last 100 lines
sudo journalctl -u chromadb -n 100

# Follow logs
sudo journalctl -u chromadb -f

# Logs since boot
sudo journalctl -u chromadb -b
```

## Advanced Configuration

### Custom Port

Edit systemd service:
```bash
sudo systemctl edit chromadb
```

Add:
```ini
[Service]
Environment="CHROMA_PORT=8001"
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart chromadb
```

### Resource Limits

Edit systemd service to add limits:
```bash
sudo systemctl edit chromadb
```

Add:
```ini
[Service]
LimitNOFILE=65536
MemoryMax=90G
```

### Multiple ChromaDB Instances

Run multiple instances on different ports:

```bash
# Instance 1
chroma run --host 0.0.0.0 --port 8000 --path ~/chromadb_data1 &

# Instance 2
chroma run --host 0.0.0.0 --port 8001 --path ~/chromadb_data2 &
```

## CLI Reference

All from Mystery machine:

```bash
# Start
sudo systemctl start chromadb
./deploy/mystery/start_services.sh

# Stop
sudo systemctl stop chromadb
pkill -f "chroma run"

# Restart
sudo systemctl restart chromadb

# Status
systemctl status chromadb
curl http://localhost:8000/api/v1/heartbeat

# Logs
sudo journalctl -u chromadb -f
tail -f ~/chromadb_logs/chromadb.log

# Monitor
watch free -h
htop
```

## Support

- **Deployment Guide**: [../README.md](../README.md)
- **Configuration**: [../../CONFIG_GUIDE.md](../../CONFIG_GUIDE.md)
- **Troubleshooting**: [../../TROUBLESHOOTING.md](../../TROUBLESHOOTING.md)

---

**Mystery Machine** | Vector Database Server | AHGA Research Processor

