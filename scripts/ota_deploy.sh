#!/bin/zsh

# OTA (Over-The-Air) Deployment Script
# Uploads code to ESP8266 via WiFi instead of USB

# Get the directory where the script is located
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
# Get the parent directory (project root)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC="$ROOT_DIR/src"

# Configuration
ESP8266_IP="${ESP8266_IP:-192.168.1.100}"  # Set via environment variable or use default
OTA_PORT="${OTA_PORT:-8266}"
OTA_PASSWORD="${OTA_PASSWORD:-pyntercom_ota_2024}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}========================================${NC}"
echo "${BLUE}  PyNtercom OTA Deployment${NC}"
echo "${BLUE}========================================${NC}"
echo ""

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "${RED}❌ Error: curl is not installed${NC}"
    echo "Install with: brew install curl"
    exit 1
fi

# Check if ESP8266 IP is set
if [ -z "$ESP8266_IP" ]; then
    echo "${RED}❌ Error: ESP8266_IP not set${NC}"
    echo "Set it with: export ESP8266_IP=192.168.1.100"
    exit 1
fi

echo "${BLUE}📡 Target Device:${NC} $ESP8266_IP:$OTA_PORT"
echo "${BLUE}🔐 Using password:${NC} ${OTA_PASSWORD:0:3}***"
echo ""

# Test connection
echo "${YELLOW}⏳ Testing connection to ESP8266...${NC}"
if ! curl -s --connect-timeout 5 "http://$ESP8266_IP:$OTA_PORT" > /dev/null 2>&1; then
    echo "${RED}❌ Cannot connect to ESP8266 at $ESP8266_IP:$OTA_PORT${NC}"
    echo "${YELLOW}💡 Make sure:${NC}"
    echo "   1. ESP8266 is powered on and connected to WiFi"
    echo "   2. OTA server is running (trigger via MQTT or manually)"
    echo "   3. IP address is correct (current: $ESP8266_IP)"
    echo "   4. Firewall allows connection"
    exit 1
fi
echo "${GREEN}✅ Connection successful${NC}"
echo ""

# Function to upload a file
upload_file() {
    local local_path="$1"
    local remote_path="$2"

    echo "${BLUE}📤 Uploading:${NC} $remote_path"

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $OTA_PASSWORD" \
        -H "X-File-Path: $remote_path" \
        -H "Content-Type: application/octet-stream" \
        --data-binary "@$local_path" \
        "http://$ESP8266_IP:$OTA_PORT/upload" 2>&1)

    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        echo "${GREEN}   ✓ Success${NC}"
        return 0
    else
        echo "${RED}   ✗ Failed (HTTP $http_code)${NC}"
        if [ ! -z "$body" ]; then
            echo "${RED}   Error: $body${NC}"
        fi
        return 1
    fi
}

# Clean cache files before deployment
echo "${YELLOW}🧹 Cleaning cache files...${NC}"
"$SCRIPT_DIR/clean.sh"
echo ""

# Upload main.py
echo "${YELLOW}📦 Deploying main.py...${NC}"
if ! upload_file "$ROOT_DIR/main.py" "main.py"; then
    echo "${RED}❌ Failed to upload main.py${NC}"
    exit 1
fi
echo ""

# Find and upload all Python files in src/
echo "${YELLOW}📦 Deploying source files...${NC}"
file_count=0
failed_count=0

# Use find to get all .py files, excluding __pycache__
while IFS= read -r file; do
    # Get path relative to ROOT_DIR
    relative_path="${file#$ROOT_DIR/}"

    if upload_file "$file" "$relative_path"; then
        ((file_count++))
    else
        ((failed_count++))
    fi
done < <(find "$SRC" -name "*.py" -not -path "*/__pycache__/*" -type f)

echo ""
echo "${BLUE}========================================${NC}"
echo "${BLUE}  Deployment Summary${NC}"
echo "${BLUE}========================================${NC}"
echo "${GREEN}✅ Successfully uploaded:${NC} $file_count files"
if [ $failed_count -gt 0 ]; then
    echo "${RED}❌ Failed uploads:${NC} $failed_count files"
    echo ""
    echo "${YELLOW}⚠️  Some files failed to upload. Check errors above.${NC}"
    exit 1
else
    echo ""
    echo "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo "${YELLOW}💡 The ESP8266 will restart automatically after OTA timeout${NC}"
    echo "${YELLOW}   or you can manually restart it via MQTT/REPL${NC}"
fi

echo ""
