#!/bin/bash

# DNS Manager Setup Script
# This script sets up the DNS Manager application with MongoDB and systemd

set -e

# Default values
MODE="none"
REINSTALL=false

# Simple argument parsing
for arg in "$@"; do
    case $arg in
        --master)
            MODE="master"
            ;;
        --slave)
            MODE="slave"
            ;;
        --reinstall)
            REINSTALL=true
            ;;
        *)
            # Ignore other args
            ;;
    esac
done

if [ "$MODE" == "none" ]; then
    echo ""
    echo "👋 Welcome to DNS Manager Setup"
    echo "This script can configure this server as a Master (Full Web UI + Watcher) or Slave (Agent)."
    echo ""
    
    echo "Select Installation Mode:"
    echo "1) Master - Install Web UI, MongoDB, and Zone Watcher"
    echo "2) Slave  - Install only Slave Agent listener"
    echo ""
    read -p "Enter choice [1/2]: " choice
    
    case $choice in
        1)
            MODE="master"
            ;;
        2)
            MODE="slave"
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# Confirm Reinstall if not specified
if [ "$REINSTALL" = false ] && [ "$MODE" == "master" ]; then
    # Check if things installed
    if [ -f ".env" ] || [ -f "docker-compose.yml" ]; then
        echo ""
        echo "⚠️  Existing configuration detected."
        read -p "Do you want to reinstall (wipe data)? [y/N] " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            REINSTALL=true
        fi
    fi
fi

echo "🚀 Starting setup in $MODE mode..."
echo ""

echo "================================================"
echo "  DNS Manager - Setup Script"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "⚠️  This script must be run as root (use sudo)"
   exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📁 Working directory: $SCRIPT_DIR"
echo ""

# ===========================
# Reinstall / Cleanup
# ===========================
if [ "$REINSTALL" = true ]; then
    echo "🧹 Cleaning up existing installation..."
    
    # Clean all services
    systemctl stop dns-manager.service 2>/dev/null || true
    systemctl disable dns-manager.service 2>/dev/null || true
    
    systemctl stop dns-watcher.service 2>/dev/null || true
    systemctl disable dns-watcher.service 2>/dev/null || true
    
    systemctl stop dns-slave-agent.service 2>/dev/null || true
    systemctl disable dns-slave-agent.service 2>/dev/null || true
    
    if [ -f "docker-compose.yml" ]; then
        docker compose down 2>/dev/null || true
        docker volume rm dns-manager_mongodb_data 2>/dev/null || true
        docker volume rm dns-manager_mongodb_config 2>/dev/null || true
    fi
    
    rm -f .env
    echo "✅ Cleanup complete"
fi

# ===========================
# Dependencies
# ===========================
echo "📦 Installing system dependencies..."

# Python
if ! command -v python3 &> /dev/null; then
    yum install -y python3 python3-pip
fi

# Docker (Only for Master)
if [ "$MODE" == "master" ]; then
    if ! command -v docker &> /dev/null; then
        echo "   Installing Docker..."
        yum install -y docker
        systemctl enable docker
        systemctl start docker
    fi
    # Check Compose
    if ! docker compose version &> /dev/null; then
        echo "⚠️  Docker Compose not found. Please install manually."
        exit 1
    fi
fi

# Virtual Environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip

# Install Python packages based on mode
if [ "$MODE" == "master" ]; then
    echo "   Installing watchdog for Master..."
    pip install watchdog requests
    pip install -r backend/requirements.txt
elif [ "$MODE" == "slave" ]; then
    pip install flask requests python-dotenv
fi

echo ""

# ===========================
# Configurations & Secrets
# ===========================
if [ ! -f ".env" ] && [ "$MODE" == "master" ]; then
    echo "🔐 Generating secrets..."
    MONGO_PASSWORD=$(openssl rand -hex 16)
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    ADMIN_PASSWORD=$(openssl rand -base64 12)
    
    cat > .env << EOF
# MongoDB Configuration
MONGO_ROOT_PASSWORD=$MONGO_PASSWORD
MONGO_URI=mongodb://dnsadmin:$MONGO_PASSWORD@localhost:27017/dns_manager?authSource=admin

# Application Settings
FLASK_ENV=production
FLASK_PORT=2020
SECRET_KEY=$SECRET_KEY

# JWT Configuration
JWT_SECRET_KEY=$JWT_SECRET
JWT_ACCESS_TOKEN_EXPIRES=3600

# DNS Configuration
NAMED_ZONE_DIR=/var/named
RNDC_PATH=/usr/sbin/rndc
SYSTEMCTL_PATH=/usr/bin/systemctl
MAX_RELOAD_ATTEMPTS=5

# Agent Config
SLAVE_SERVERS=
SLAVE_API_PORT=5000
SLAVE_SECRET=$(openssl rand -hex 16)

# Default Admin Credentials
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=$ADMIN_PASSWORD
EOF
    echo "✅ .env file created"
fi

# Slave needs a simpler config or just uses defaults
# We can create a lightweight config for slave agent if needed, but not strictly required by agent code currently
# Agent uses config.py which loads .env, so let's create a minimal .env for slave

if [ ! -f ".env" ] && [ "$MODE" == "slave" ]; then
    echo "📝 Configuring Slave Agent..."
    read -p "Enter SLAVE_SECRET (must match Master): " SLAVE_SECRET
    if [ -z "$SLAVE_SECRET" ]; then
        SLAVE_SECRET="changeme"
        echo "⚠️  Using default secret: changeme"
    fi
    
    cat > .env << EOF
SLAVE_API_PORT=5000
SLAVE_SECRET=$SLAVE_SECRET
SLAVE_DIR=/var/named/slaves
SYSTEMCTL_PATH=/usr/bin/systemctl
EOF
    echo "✅ Slave .env created"
fi

echo ""

# ===========================
# Service Installation
# ===========================

if [ "$MODE" == "master" ]; then
    # 1. MongoDB
    echo "🐳 Starting MongoDB..."
    sed -i "s/MONGO_ROOT_PASSWORD:-.*}/MONGO_ROOT_PASSWORD:-$MONGO_PASSWORD}/" docker-compose.yml
    docker compose up -d
    
    # Wait for Mongo...
    echo "⏳ Waiting for DB..."
    sleep 10 
    
    # 2. Create Admin User
    echo "👤 Creating Admin User..."
    python3 << PYTHON_SCRIPT
import os
import sys
sys.path.insert(0, '$SCRIPT_DIR/backend')
from models import User
from dotenv import load_dotenv
load_dotenv()
User.create_indexes()
result = User.create(os.getenv('DEFAULT_ADMIN_USERNAME'), os.getenv('DEFAULT_ADMIN_PASSWORD'), role='admin')
if result.get('success'): print("✅ Admin Created")
PYTHON_SCRIPT

    # 3. Master Service (Web App)
    echo "⚙️  Installing DNS Manager Service..."
    cat > /etc/systemd/system/dns-manager.service << EOF
[Unit]
Description=DNS Manager Web UI
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR/backend
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable dns-manager
    systemctl restart dns-manager
    
    # 4. Watcher Service (Master)
    echo "⚙️  Installing DNS Watcher Service..."
    cat > /etc/systemd/system/dns-watcher.service << EOF
[Unit]
Description=DNS Zone Watcher (Master)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR/backend
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python watcher.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable dns-watcher
    systemctl restart dns-watcher

elif [ "$MODE" == "slave" ]; then
    # Slave Service
    echo "⚙️  Installing Slave Agent Service..."
    cat > /etc/systemd/system/dns-slave-agent.service << EOF
[Unit]
Description=DNS Slave Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR/backend
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python slave_agent.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable dns-slave-agent
    systemctl restart dns-slave-agent
fi

echo ""
echo "================================================"
echo "  ✅ Setup Complete: $MODE Mode"
echo "================================================"

if [ "$MODE" == "master" ]; then
    echo "📍 Web Interface: http://$(hostname -I | awk '{print $1}'):2020"
    echo "🔑 Admin Password: $ADMIN_PASSWORD"
    echo "📋 Credentials saved to: /var/passwords/dns-manager-credentials.txt"
    
    # Save creds
    mkdir -p /var/passwords
    echo "DNS Manager Credentials" > /var/passwords/dns-manager-credentials.txt
    echo "Admin: admin / $ADMIN_PASSWORD" >> /var/passwords/dns-manager-credentials.txt
    chmod 600 /var/passwords/dns-manager-credentials.txt
    
    echo "ℹ️  Remember to configure SLAVE_SERVERS in .env"

elif [ "$MODE" == "slave" ]; then
    echo "🤖 Slave Agent listening on port 5000"
    echo "🔑 Secret: $SLAVE_SECRET"
    echo "ℹ️  Update Master .env with this server IP and Secret."
fi
echo ""

echo "🔄 To reinstall everything:"
echo "   sudo bash setup.sh --reinstall"
echo ""
echo "================================================"
