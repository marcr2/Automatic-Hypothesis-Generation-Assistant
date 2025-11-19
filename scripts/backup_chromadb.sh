#!/bin/bash

#############################################################################
# Backup ChromaDB from Mystery to M3
# Creates compressed backup and stores on M3 for safe keeping
#############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Backup ChromaDB: Mystery → M3${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Configuration
MYSTERY_IP="${1:-${CHROMA_HOST}}"
MYSTERY_USER="${2:-${USER}}"
MYSTERY_DATA_DIR="${3:-/home/${MYSTERY_USER}/chromadb_data}"
BACKUP_DIR="${4:-data/backups}"
BACKUP_NAME="chromadb_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
KEEP_BACKUPS=5  # Number of backups to keep

# Validate inputs
if [ -z "$MYSTERY_IP" ] || [ "$MYSTERY_IP" == "MYSTERY_IP_ADDRESS" ]; then
    echo -e "${RED}❌ Mystery IP address not configured${NC}"
    echo "Usage: $0 [mystery_ip] [mystery_user] [mystery_data_dir] [backup_dir]"
    echo "Example: $0 192.168.1.100 user /home/user/chromadb_data data/backups"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Mystery machine: $MYSTERY_USER@$MYSTERY_IP"
echo "Data directory: $MYSTERY_DATA_DIR"
echo "Backup location: $BACKUP_DIR/$BACKUP_NAME"
echo ""

# Check if ChromaDB is running on Mystery
echo -e "${YELLOW}⚠️  Note: ChromaDB should be stopped for consistent backup${NC}"
read -p "Stop ChromaDB on Mystery? (y/n) " -n 1 -r
echo
STOP_CHROMADB=$REPLY

if [[ $STOP_CHROMADB =~ ^[Yy]$ ]]; then
    echo "Stopping ChromaDB on Mystery..."
    ssh "$MYSTERY_USER@$MYSTERY_IP" "sudo systemctl stop chromadb 2>/dev/null || pkill -f 'chroma run'"
    sleep 3
    echo -e "${GREEN}✅${NC} ChromaDB stopped"
fi

# Create backup on Mystery
echo -e "\n${GREEN}==>${NC} Creating backup on Mystery..."
ssh "$MYSTERY_USER@$MYSTERY_IP" "cd $MYSTERY_DATA_DIR && tar -czf /tmp/$BACKUP_NAME ./*"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to create backup on Mystery${NC}"
    exit 1
fi

# Copy backup to M3
echo -e "\n${GREEN}==>${NC} Copying backup to M3..."
rsync -avz --progress \
    "$MYSTERY_USER@$MYSTERY_IP:/tmp/$BACKUP_NAME" \
    "$BACKUP_DIR/"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to copy backup${NC}"
    exit 1
fi

# Clean up remote backup
ssh "$MYSTERY_USER@$MYSTERY_IP" "rm /tmp/$BACKUP_NAME"

# Restart ChromaDB if we stopped it
if [[ $STOP_CHROMADB =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}==>${NC} Restarting ChromaDB on Mystery..."
    ssh "$MYSTERY_USER@$MYSTERY_IP" "sudo systemctl start chromadb 2>/dev/null || nohup ~/chromadb_venv/bin/chroma run --host 0.0.0.0 --port \${CHROMA_PORT:-8000} --path $MYSTERY_DATA_DIR > ~/chromadb_logs/chromadb.log 2>&1 &"
    sleep 3
    echo -e "${GREEN}✅${NC} ChromaDB restarted"
fi

# Get backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)

echo -e "\n${GREEN}✅ Backup completed successfully${NC}"
echo ""
echo "Backup file: $BACKUP_DIR/$BACKUP_NAME"
echo "Size: $BACKUP_SIZE"

# Clean old backups
echo -e "\n${GREEN}==>${NC} Cleaning old backups (keeping last $KEEP_BACKUPS)..."
cd "$BACKUP_DIR"
ls -t chromadb_backup_*.tar.gz 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm
echo "Current backups:"
ls -lh chromadb_backup_*.tar.gz 2>/dev/null || echo "No backups found"

echo ""
echo -e "${BLUE}To restore this backup:${NC}"
echo "1. Stop ChromaDB on Mystery: ssh $MYSTERY_USER@$MYSTERY_IP 'sudo systemctl stop chromadb'"
echo "2. Clear data: ssh $MYSTERY_USER@$MYSTERY_IP 'rm -rf $MYSTERY_DATA_DIR/*'"
echo "3. Copy backup: scp $BACKUP_DIR/$BACKUP_NAME $MYSTERY_USER@$MYSTERY_IP:/tmp/"
echo "4. Extract: ssh $MYSTERY_USER@$MYSTERY_IP 'cd $MYSTERY_DATA_DIR && tar -xzf /tmp/$BACKUP_NAME'"
echo "5. Restart: ssh $MYSTERY_USER@$MYSTERY_IP 'sudo systemctl start chromadb'"

