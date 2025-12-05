#!/bin/bash
# DNS Manager Troubleshooting Script
# Run this on your server to diagnose the network error

echo "🔍 DNS Manager Troubleshooting"
echo "================================"
echo ""

# 1. Check if DNS Manager service is running
echo "1️⃣ Checking DNS Manager service status..."
if systemctl is-active --quiet dns-manager.service; then
    echo "✅ Service is running"
else
    echo "❌ Service is NOT running!"
    echo ""
    echo "Starting service..."
    sudo systemctl start dns-manager.service
    sleep 3
fi
echo ""

# 2. Check service logs for errors
echo "2️⃣ Recent service logs:"
echo "---"
sudo journalctl -u dns-manager.service -n 20 --no-pager
echo ""

# 3. Check if Flask is listening on port 2020
echo "3️⃣ Checking if Flask is listening on port 2020..."
if netstat -tuln | grep -q ":2020"; then
    echo "✅ Port 2020 is listening"
    netstat -tuln | grep ":2020"
else
    echo "❌ Port 2020 is NOT listening!"
fi
echo ""

# 4. Test API endpoint locally
echo "4️⃣ Testing API health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:2020/api/health || echo "FAILED")
if echo "$HEALTH_RESPONSE" | grep -q "success"; then
    echo "✅ API is responding: $HEALTH_RESPONSE"
else
    echo "❌ API not responding: $HEALTH_RESPONSE"
fi
echo ""

# 5. Check MongoDB connection
echo "5️⃣ Checking MongoDB status..."
if docker ps | grep -q dns-manager-mongodb; then
    echo "✅ MongoDB container is running"
    
    # Test MongoDB connection
    MONGO_PASS=$(grep MONGO_ROOT_PASSWORD /root/dns-manager/.env | cut -d'=' -f2)
    if docker exec dns-manager-mongodb mongosh admin -u admin -p "$MONGO_PASS" --eval "db.version()" --quiet > /dev/null 2>&1; then
        echo "✅ MongoDB is accessible"
    else
        echo "❌ MongoDB connection failed"
    fi
else
    echo "❌ MongoDB container is NOT running!"
fi
echo ""

# 6. Check firewall (if applicable)
echo "6️⃣ Checking firewall status..."
if command -v firewall-cmd &> /dev/null; then
    if firewall-cmd --state 2>/dev/null | grep -q "running"; then
        echo "⚠️  Firewall is running"
        echo "Checking if port 2020 is open..."
        if firewall-cmd --list-ports | grep -q "2020"; then
            echo "✅ Port 2020 is allowed in firewall"
        else
            echo "❌ Port 2020 is NOT allowed in firewall!"
            echo "Run: sudo firewall-cmd --permanent --add-port=2020/tcp"
            echo "     sudo firewall-cmd --reload"
        fi
    else
        echo "✅ Firewall is not running"
    fi
else
    echo "✅ No firewall detected"
fi
echo ""

# 7. Test from external IP
echo "7️⃣ Server IP addresses:"
hostname -I
echo ""

# 8. Summary and recommendations
echo "================================"
echo "📋 SUMMARY"
echo "================================"
echo ""
echo "If API health check failed:"
echo "  1. Check logs above for Python errors"
echo "  2. Verify .env file exists: ls -la /root/dns-manager/.env"
echo "  3. Restart service: sudo systemctl restart dns-manager.service"
echo ""
echo "If MongoDB connection failed:"
echo "  1. Restart MongoDB: cd /root/dns-manager && docker compose restart"
echo "  2. Check MongoDB logs: docker logs dns-manager-mongodb"
echo ""
echo "If port 2020 not listening:"
echo "  1. Check Python errors in logs above"
echo "  2. Verify config.py has correct port"
echo "  3. Check if another process is using port 2020: lsof -i :2020"
echo ""
echo "Access URL should be: http://YOUR_SERVER_IP:2020"
echo ""
