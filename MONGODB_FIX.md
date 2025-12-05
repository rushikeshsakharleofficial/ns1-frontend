# MongoDB Authentication Fix - Quick Guide

## Problem
MongoDB authentication was failing because:
- `docker-compose.yml` had `MONGO_INITDB_ROOT_USERNAME: dnsadmin`  
- This conflicted with `init-mongo.js` trying to create an application user also named `dnsadmin`

## Solution
Updated configuration files:
- **docker-compose.yml**: Root user changed to `admin`
- **init-mongo.js**: Creates `dnsadmin` application user with proper permissions
- **setup.sh**: Added `--reinstall` flag for easy reconfiguration

## How to Fix on Your Server

### Option 1: Use the Reinstall Flag (Recommended)

```bash
cd /root/dns-manager

# Copy the updated files from your Windows machine to the server
# (docker-compose.yml, init-mongo.js, setup.sh)

# Run setup with reinstall flag
sudo bash setup.sh --reinstall
```

This will:
- ✅ Stop the DNS Manager service
- ✅ Stop and remove MongoDB containers
- ✅ Delete MongoDB volumes (fresh start)
- ✅ Remove .env file (regenerate with new passwords)
- ✅ Reinstall everything from scratch
- ✅ Create new admin user

### Option 2: Manual Steps

```bash
cd /root/dns-manager

# 1. Stop services
sudo systemctl stop dns-manager.service
docker-compose down

# 2. Remove volumes
docker volume rm dns-manager_mongodb_data dns-manager_mongodb_config

# 3. Remove old .env
rm -f .env

# 4. Run normal setup
sudo bash setup.sh
```

## After Installation

**New MongoDB Credentials:**
- Root User: `admin` / (password from `.env`)
- App User: `dnsadmin` / (same password from `.env`)

**Test Connection:**
```bash
# Test with admin user
docker exec -it dns-manager-mongodb mongosh admin -u admin -p "YOUR_PASSWORD"

# Check if dnsadmin user exists
db.getUser('dnsadmin')
```

**Access Application:**
```
http://YOUR_SERVER_IP:2020
```

## What Changed

| File | Change | Reason |
|------|--------|--------|
| `docker-compose.yml` | Root user: `admin` (was `dnsadmin`) | Avoid username conflict |
| `init-mongo.js` | Creates `dnsadmin` in admin DB | Proper user creation |
| `setup.sh` | Added `--reinstall` flag | Easy reconfiguration |

## Troubleshooting

**If you still get authentication errors:**

```bash
# Check MongoDB logs
docker logs dns-manager-mongodb --tail 100

# Check Flask app logs  
sudo journalctl -u dns-manager.service -n 50

# Verify users in MongoDB
docker exec -it dns-manager-mongodb mongosh admin -u admin -p "PASSWORD" --eval "db.getUsers()"
```

**Check .env file:**
```bash
cat /root/dns-manager/.env | grep MONGO
```

Should show:
```
MONGO_ROOT_PASSWORD=<some_hash>
MONGO_URI=mongodb://dnsadmin:<same_hash>@localhost:27017/dns_manager?authSource=admin
```
