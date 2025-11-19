#!/bin/bash

#############################################################################
# Sync Embeddings from M3 to Mystery
# Optional script to copy embeddings for local processing on Mystery
#############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Sync Embeddings: M3 → Mystery${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Configuration
SOURCE_DIR="${1:-data/embeddings/}"
MYSTERY_IP="${2:-${CHROMA_HOST}}"
MYSTERY_USER="${3:-${USER}}"
DEST_DIR="${4:-/home/${MYSTERY_USER}/embeddings/}"

# Validate inputs
if [ -z "$MYSTERY_IP" ] || [ "$MYSTERY_IP" == "MYSTERY_IP_ADDRESS" ]; then
    echo -e "${RED}❌ Mystery IP address not configured${NC}"
    echo "Usage: $0 [source_dir] [mystery_ip] [mystery_user] [dest_dir]"
    echo "Example: $0 data/embeddings/ 192.168.1.100 user /home/user/embeddings/"
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Source directory not found: $SOURCE_DIR${NC}"
    exit 1
fi

# Calculate size
SOURCE_SIZE=$(du -sh "$SOURCE_DIR" | cut -f1)
echo "Source directory: $SOURCE_DIR"
echo "Size: $SOURCE_SIZE"
echo "Destination: $MYSTERY_USER@$MYSTERY_IP:$DEST_DIR"
echo ""

# Confirm
read -p "Proceed with sync? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Sync cancelled"
    exit 0
fi

# Perform sync
echo -e "\n${GREEN}==>${NC} Syncing embeddings..."

rsync -avz --progress \
    --human-readable \
    --stats \
    "$SOURCE_DIR" \
    "$MYSTERY_USER@$MYSTERY_IP:$DEST_DIR"

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Sync completed successfully${NC}"
else
    echo -e "\n${RED}❌ Sync failed${NC}"
    exit 1
fi

echo ""
echo "Synced to: $MYSTERY_USER@$MYSTERY_IP:$DEST_DIR"
echo "Verify on Mystery: ssh $MYSTERY_USER@$MYSTERY_IP 'ls -lh $DEST_DIR'"

