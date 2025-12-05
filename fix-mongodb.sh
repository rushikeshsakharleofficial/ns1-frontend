#!/bin/bash
# MongoDB Fix Deployment Script
# Run this on your DNS server to fix the authentication issue

set -e

echo "🔧 Fixing MongoDB Authentication Issue..."

cd /root/dns-manager

# 1. Stop current containers
echo "📦 Stopping Docker containers..."
docker compose down

# 2. Remove old volumes (this will delete existing data)
echo "🗑️  Removing old MongoDB volumes..."
docker volume rm dns-manager_mongodb_data dns-manager_mongodb_config 2>/dev/null || true

# 3. Verify .env file has correct settings
echo "✓ Checking .env configuration..."
if ! grep -q "MONGO_ROOT_PASSWORD=" .env; then
    echo "❌ Error: MONGO_ROOT_PASSWORD not found in .env"
    exit 1
fi

# 4. Start fresh MongoDB with fixed config
echo "🚀 Starting MongoDB with corrected configuration..."
docker compose up -d

# 5. Wait for MongoDB to initialize
echo "⏳ Waiting for MongoDB initialization (15 seconds)..."
sleep 15

# 6. Verify MongoDB is running
echo "🔍 Checking MongoDB status..."
docker ps | grep dns-manager-mongodb || {
    echo "❌ MongoDB container not running!"
    docker logs dns-manager-mongodb --tail 50
    exit 1
}

# 7. Test MongoDB connection
echo "🧪 Testing MongoDB connection..."
MONGO_PASS=$(grep MONGO_ROOT_PASSWORD .env | cut -d'=' -f2)
docker exec dns-manager-mongodb mongosh admin -u admin -p "$MONGO_PASS" --eval "db.version()" --quiet || {
    echo "❌ MongoDB connection test failed!"
    exit 1
}

echo "✓ MongoDB admin connection successful"

# 8. Verify dnsadmin user was created
echo "🔍 Verifying dnsadmin user..."
docker exec dns-manager-mongodb mongosh admin -u admin -p "$MONGO_PASS" --eval "db.getUser('dnsadmin')" --quiet || {
    echo "❌ dnsadmin user not found!"
    exit 1
}

echo "✓ dnsadmin user verified"

# 9. Restart Flask application
echo "🔄 Restarting DNS Manager service..."
sudo systemctl restart dns-manager.service

# 10. Wait a moment for service to start
sleep 3

# 11. Check service status
echo "📊 Checking DNS Manager service status..."
sudo systemctl status dns-manager.service --no-pager -l

# 12. Show recent logs
echo ""
echo "📜 Recent application logs:"
sudo journalctl -u dns-manager.service -n 20 --no-pager

echo ""
echo "✅ MongoDB fix deployment complete!"
echo "🌐 You can now access the application at http://YOUR_SERVER_IP:2020"
echo ""
echo "📝 Summary of changes:"
echo "   - MongoDB root user: admin (was: dnsadmin)"  
echo "   - MongoDB app user: dnsadmin"
echo "   - Both use password from MONGO_ROOT_PASSWORD in .env"
