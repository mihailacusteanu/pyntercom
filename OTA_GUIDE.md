# OTA (Over-The-Air) Update Guide

Complete guide for deploying code updates to ESP8266 via WiFi instead of USB.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Initial Setup](#initial-setup)
3. [Triggering OTA Mode](#triggering-ota-mode)
4. [Deploying Code](#deploying-code)
5. [Security](#security)
6. [Troubleshooting](#troubleshooting)

---

## Overview

OTA (Over-The-Air) updates allow you to deploy code changes to your ESP8266 intercom via WiFi, eliminating the need for physical USB access. This is essential for production deployments where the device is physically installed.

**Benefits:**
- ✅ No need to physically access the device
- ✅ Deploy from anywhere on the network
- ✅ Faster deployment (no USB cable unplugging)
- ✅ Can update multiple devices remotely

**How it works:**
1. ESP8266 runs a simple HTTP server for file uploads
2. Your computer sends files via WiFi
3. ESP8266 writes files to filesystem
4. ESP8266 restarts with new code

---

## Initial Setup

### 1. First-Time Deployment (USB Required)

For the first deployment, you need USB to install the OTA system:

```bash
# Deploy initial code with OTA support
./scripts/deploy.sh

# Or manually copy main_with_ota.py as main.py
cp main_with_ota.py main.py
./scripts/deploy.sh
```

### 2. Configure ESP8266 IP Address

Find your ESP8266's IP address (check your router or use MQTT logs) and set it:

```bash
export ESP8266_IP=192.168.1.100  # Replace with your device's IP
```

To make this permanent, add to your `~/.zshrc` or `~/.bashrc`:

```bash
echo 'export ESP8266_IP=192.168.1.100' >> ~/.zshrc
source ~/.zshrc
```

### 3. Configure OTA Password (Optional but Recommended)

Default password: `pyntercom_ota_2024`

To change:

1. Edit `src/app/ota.py` and change the default password
2. Edit `main_with_ota.py` and update the password
3. Set environment variable for deployment script:

```bash
export OTA_PASSWORD="your_secure_password_here"
```

---

## Triggering OTA Mode

The ESP8266 needs to enter OTA mode before you can deploy. There are three ways to trigger this:

### Method 1: Via MQTT (Recommended for Production)

Send a message to the OTA topic from Home Assistant or any MQTT client:

**Using Home Assistant:**
```yaml
# In Developer Tools > Services
service: mqtt.publish
data:
  topic: "pyntercom/ota"
  payload: "start_ota"
```

**Using mosquitto_pub:**
```bash
mosquitto_pub -h YOUR_MQTT_BROKER -t "pyntercom/ota" -m "start_ota"
```

### Method 2: Via REPL (Development)

Connect to ESP8266 REPL and run:

```bash
./scripts/repl.sh
```

Then in REPL:
```python
from src.app.ota import start_ota_mode
start_ota_mode()
```

### Method 3: Create a Standalone OTA Script

Create `ota_only.py` on ESP8266:

```python
from src.app.ota import start_ota_mode
start_ota_mode(timeout=600)  # 10 minutes
```

Deploy it once via USB, then trigger via:
```bash
./scripts/repl.sh
# Then type: import ota_only
```

---

## Deploying Code

Once OTA mode is active:

### Basic Deployment

```bash
./scripts/ota_deploy.sh
```

### With Custom Configuration

```bash
# Set custom IP, port, and password
export ESP8266_IP=192.168.1.150
export OTA_PORT=8266
export OTA_PASSWORD=my_secure_password

./scripts/ota_deploy.sh
```

### What Gets Deployed

The script automatically uploads:
- ✅ `main.py` - Entry point
- ✅ All `.py` files in `src/` directory
- ✅ Preserves directory structure
- ❌ Excludes `__pycache__` and `.pyc` files

### Deployment Output

```
========================================
  PyNtercom OTA Deployment
========================================

📡 Target Device: 192.168.1.100:8266
🔐 Using password: pyn***
⏳ Testing connection to ESP8266...
✅ Connection successful

🧹 Cleaning cache files...
📦 Deploying main.py...
   ✓ Success

📦 Deploying source files...
📤 Uploading: src/app/intercom.py
   ✓ Success
📤 Uploading: src/app/ota.py
   ✓ Success
... (continues for all files)

========================================
  Deployment Summary
========================================
✅ Successfully uploaded: 25 files
🎉 Deployment completed successfully!
```

### After Deployment

The ESP8266 will:
1. Continue running OTA server until timeout (5 minutes default)
2. Auto-shutdown OTA server
3. Restart ESP8266
4. Load new code
5. Resume normal intercom operation

---

## Security

### Important Security Considerations

1. **Change the Default Password!**
   - Default: `pyntercom_ota_2024`
   - Change in: `src/app/ota.py` and `main_with_ota.py`

2. **OTA Port is Exposed**
   - Port 8266 is open when OTA is active
   - Only activate OTA when needed
   - Use firewall rules to restrict access

3. **Auto-Timeout Protection**
   - OTA server auto-shuts down after 5 minutes
   - Prevents indefinite exposure
   - Configurable in code

4. **Network Security**
   - Use WPA2/WPA3 WiFi encryption
   - Put ESP8266 on isolated VLAN if possible
   - Don't expose OTA port to internet

### Recommended Security Setup

```python
# In main_with_ota.py
start_ota_mode(
    port=8266,
    password="YOUR_STRONG_PASSWORD_HERE",  # Use strong password
    timeout=180  # Reduce to 3 minutes
)
```

---

## Troubleshooting

### Cannot Connect to ESP8266

**Symptoms:**
```
❌ Cannot connect to ESP8266 at 192.168.1.100:8266
```

**Solutions:**
1. ✅ Verify ESP8266 is powered on
2. ✅ Verify ESP8266 is connected to WiFi (check MQTT logs)
3. ✅ Verify IP address is correct:
   ```bash
   ping 192.168.1.100
   ```
4. ✅ Verify OTA mode is active (send MQTT trigger again)
5. ✅ Check firewall isn't blocking port 8266
6. ✅ Try from same WiFi network as ESP8266

### Upload Fails (HTTP 401 Unauthorized)

**Symptoms:**
```
✗ Failed (HTTP 401)
Error: Missing or invalid authorization
```

**Solutions:**
1. ✅ Verify OTA_PASSWORD environment variable matches password in code
2. ✅ Check password in `src/app/ota.py`
3. ✅ Check password in `main_with_ota.py`

### Upload Fails (HTTP 403 Forbidden)

**Symptoms:**
```
✗ Failed (HTTP 403)
Error: Invalid password
```

**Solutions:**
1. ✅ Password is incorrect
2. ✅ Update `OTA_PASSWORD` environment variable:
   ```bash
   export OTA_PASSWORD="correct_password"
   ```

### Partial Upload / Timeout

**Symptoms:**
```
📤 Uploading: src/app/intercom.py
   ✗ Failed (HTTP )
   Error: (timeout or empty response)
```

**Solutions:**
1. ✅ ESP8266 ran out of memory - restart and try again
2. ✅ WiFi signal is weak - move closer to router
3. ✅ Increase timeout in `ota_deploy.sh`:
   ```bash
   curl --connect-timeout 30 ...  # Increase from 5 to 30
   ```

### ESP8266 Doesn't Restart After OTA

**Expected Behavior:**
- OTA server runs for 5 minutes
- Auto-shuts down
- ESP8266 restarts automatically

**If Not Restarting:**
1. ✅ Wait for full timeout (5 minutes)
2. ✅ Manually restart via MQTT:
   ```yaml
   service: mqtt.publish
   data:
     topic: "pyntercom/restart"
     payload: "restart_now"
   ```
3. ✅ Or use REPL:
   ```python
   import machine
   machine.reset()
   ```

### OTA Server Not Starting

**Check REPL output:**
```bash
./scripts/repl.sh
```

Look for error messages. Common issues:
- ❌ Not enough memory (restart ESP8266)
- ❌ Port 8266 already in use (restart ESP8266)
- ❌ WiFi not connected (check config)

---

## Advanced Usage

### Custom OTA Port

```bash
# Change port in src/app/ota.py
port=9999

# Set environment variable
export OTA_PORT=9999

# Deploy
./scripts/ota_deploy.sh
```

### Longer OTA Timeout

```python
# In main_with_ota.py
start_ota_mode(
    timeout=600  # 10 minutes instead of 5
)
```

### OTA Status Check

Create a helper to check if OTA is active:

```bash
curl -s http://192.168.1.100:8266 && echo "OTA is active" || echo "OTA is not active"
```

### Deploy Specific Files Only

Modify `ota_deploy.sh` to upload specific files:

```bash
# Upload only one file
upload_file "$ROOT_DIR/src/app/intercom.py" "src/app/intercom.py"
```

---

## Comparison: USB vs OTA Deployment

| Feature | USB (`deploy.sh`) | OTA (`ota_deploy.sh`) |
|---------|-------------------|------------------------|
| **Physical Access** | Required | Not required |
| **Speed** | ~30 seconds | ~45 seconds |
| **Setup** | Plug in USB | Trigger via MQTT |
| **Network** | Not needed | Must be on WiFi |
| **Security** | Physical security | Password protected |
| **Best For** | Initial setup, debugging | Production updates |

---

## Quick Reference

### Environment Variables

```bash
export ESP8266_IP=192.168.1.100      # ESP8266 IP address
export OTA_PORT=8266                 # OTA server port (default: 8266)
export OTA_PASSWORD=pyntercom_ota_2024  # OTA password
```

### Common Commands

```bash
# Trigger OTA via MQTT
mosquitto_pub -h broker -t "pyntercom/ota" -m "start_ota"

# Deploy via OTA
./scripts/ota_deploy.sh

# Check if OTA is active
curl http://192.168.1.100:8266

# Connect to REPL
./scripts/repl.sh
```

### File Locations

- **OTA Server Code**: `src/app/ota.py`
- **OTA Deployment Script**: `scripts/ota_deploy.sh`
- **Main with OTA**: `main_with_ota.py`
- **This Guide**: `OTA_GUIDE.md`

---

## Next Steps

1. ✅ Deploy `main_with_ota.py` via USB (first time only)
2. ✅ Set `ESP8266_IP` environment variable
3. ✅ Change default OTA password
4. ✅ Test OTA deployment
5. ✅ Add to your deployment workflow

**Happy wireless deploying! 🚀**
