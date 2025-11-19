#!/bin/bash

#############################################################################
# Restore ChromaDB Backup from M3 to Mystery
# Restores a previously created backup
#############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Restore ChromaDB: M3 → Mystery${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Configuration
BACKUP_FILE="$1"
MYSTERY_IP="${2:-${CHROMA_HOST}}"
MYSTERY_USER="${3:-${USER}}"
MYSTERY_DATA_DIR="${4:-/home/${MYSTERY_USER}/chromadb_data}"

# Validate inputs
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${YELLOW}Available backups:${NC}"
    ls -lh data/backups/chromadb_backup_*.tar.gz 2>/dev/null || echo "No backups found"
    echo ""
    echo "Usage: $0 <backup_file> [mystery_ip] [mystery_user] [mystery_data_dir]"
    echo "Example: $0 data/backups/chromadb_backup_20251119.tar.gz 192.168.1.100"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

if [ -z "$MYSTERY_IP" ] || [ "$MYSTERY_IP" == "MYSTERY_IP_ADDRESS" ]; then
    echo -e "${RED}❌ Mystery IP address not configured${NC}"
    exit 1
fi

BACKUP_SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)

echo -e "${YELLOW}⚠️  WARNING: This will replace all data in ChromaDB!${NC}"
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Size: $BACKUP_SIZE"
echo "Mystery machine: $MYSTERY_USER@$MYSTERY_IP"
echo "Data directory: $MYSTERY_DATA_DIR"
echo ""

read -p "Are you sure you want to proceed? (yes/no) " -r
if [[ ! $REPLY == "yes" ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop ChromaDB on Mystery
echo -e "\n${GREEN}==>${NC} Stopping ChromaDB on Mystery..."
ssh "$MYSTERY_USER@$MYSTERY_IP" "sudo systemctl stop chromadb 2>/dev/null || pkill -f 'chroma run'"
sleep 3

# Backup current data (just in case)
echo -e "\n${GREEN}==>${NC} Creating safety backup of current data..."
ssh "$MYSTERY_USER@$MYSTERY_IP" "cd $MYSTERY_DATA_DIR && tar -czf /tmp/chromadb_pre_restore_$(date +%Y%m%d_%H%M%S).tar.gz ./* 2>/dev/null || true"

# Clear existing data
echo -e "\n${GREEN}==>${NC} Clearing existing data..."
ssh "$MYSTERY_USER@$MYSTERY_IP" "rm -rf $MYSTERY_DATA_DIR/*"

# Copy backup to Mystery
echo -e "\n${GREEN}==>${NC} Copying backup to Mystery..."
rsync -avz --progress \
    "$BACKUP_FILE" \
    "$MYSTERY_USER@$MYSTERY_IP:/tmp/chromadb_restore.tar.gz"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to copy backup${NC}"
    exit 1
fi

# Extract backup
echo -e "\n${GREEN}==>${NC} Extracting backup..."
ssh "$MYSTERY_USER@$MYSTERY_IP" "cd $MYSTERY_DATA_DIR && tar -xzf /tmp/chromadb_restore.tar.gz"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to extract backup${NC}"
    exit 1
fi

# Clean up
ssh "$MYSTERY_USER@$MYSTERY_IP" "rm /tmp/chromadb_restore.tar.gz"

# Restart ChromaDB
echo -e "\n${GREEN}==>${NC} Restarting ChromaDB..."
ssh "$MYSTERY_USER@$MYSTERY_IP" "sudo systemctl start chromadb 2>/dev/null || nohup ~/chromadb_venv/bin/chroma run --host 0.0.0.0 --port \${CHROMA_PORT:-8000} --path $MYSTERY_DATA_DIR > ~/chromadb_logs/chromadb.log 2>&1 &"
sleep 5

# Test connection
echo -e "\n${GREEN}==>${NC} Testing connection..."
if ssh "$MYSTERY_USER@$MYSTERY_IP" "curl -s http://localhost:\${CHROMA_PORT:-8000}/api/v1/heartbeat" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ChromaDB is responding${NC}"
else
    echo -e "${YELLOW}⚠️  ChromaDB may still be starting...${NC}"
fi

echo -e "\n${GREEN}✅ Restore completed successfully${NC}"
echo ""
echo "Safety backup of previous data: /tmp/chromadb_pre_restore_*.tar.gz (on Mystery)"
echo "Remove it when you're sure the restore is successful"

