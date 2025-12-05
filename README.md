# DNS Manager Dashboard

A modern, premium web application for managing BIND DNS server entries with MongoDB-backed authentication and comprehensive event logging.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![MongoDB](https://img.shields.io/badge/mongodb-7.0-green.svg)

## Features

✨ **Premium Modern UI**: Dark theme with glassmorphism effects and smooth animations  
🔐 **Secure Authentication**: JWT-based authentication with role-based access control  
📝 **Comprehensive DNS Management**: Support for A, AAAA, MX, TXT, SRV, CNAME, PTR, and NS records  
🔄 **Automatic Zone Reload**: `rndc reload` with retry logic (up to 5 attempts)  
🚀 **Service Management**: Restart named service (admin only)  
📊 **Event Logging**: Complete audit trail of all DNS changes  
🌍 **Zone Management**: Manage both forward and reverse DNS zones  
⚡ **Real-time Updates**: Instant feedback on all operations

## Technology Stack

### Backend
- **Python 3.8+** with Flask web framework
- **MongoDB 7.0** for user authentication and event logging
- **JWT** for secure token-based authentication
- **bcrypt** for password hashing

### Frontend
- **Modern HTML5/CSS3/JavaScript** (no frameworks)
- **Glassmorphism UI** with dark theme
- **Responsive design** for desktop and mobile
- **Inter font** from Google Fonts

### Infrastructure
- **Docker** for MongoDB containerization
- **systemd** for application service management
- **BIND named** integration via `rndc`

## Quick Start

### Prerequisites

- RHEL/CentOS/AlmaLinux 9
- Root access
- BIND named server installed and configured
- Internet connection for downloading dependencies

### Installation

1. Clone or copy this repository to your server (e.g., `/root/ns1`)

2. Run the setup script:

```bash
cd /root/ns1
chmod +x setup.sh
sudo ./setup.sh
```

The setup script will:
- Install Python 3, Docker, and Docker Compose
- Create a Python virtual environment
- Generate secure random passwords
- Start MongoDB container
- Create the default admin user
- Install and start the systemd service

3. Access the web interface:

```
http://YOUR_SERVER_IP:2020
```

Default credentials will be displayed after setup completes.

## Configuration

### Environment Variables

All configuration is stored in `.env` file. Key settings:

```env
# MongoDB Connection
MONGO_URI=mongodb://dnsadmin:PASSWORD@localhost:27017/dns_manager?authSource=admin

# Application Port
FLASK_PORT=2020

# DNS Paths
NAMED_ZONE_DIR=/var/named
RNDC_PATH=/usr/sbin/rndc
SYSTEMCTL_PATH=/usr/bin/systemctl

# Reload Retry Settings
MAX_RELOAD_ATTEMPTS=5
```

### Zone File Patterns

The application automatically detects zone files based on these patterns:
- **Forward zones**: `*.hosts` (e.g., `linuxhardened.com.hosts`)
- **Reverse zones**: `*.rev` (e.g., `172.236.173.rev`)

## Usage

### Managing DNS Records

1. **Login** with your admin credentials
2. **Select a zone** from the dropdown menu
3. **Add/Edit/Delete** DNS records using the intuitive interface
4. **Reload the zone** to apply changes with automatic retry logic
5. **View event logs** to track all changes

### Supported Record Types

| Type | Description | Fields |
|------|-------------|--------|
| **A** | IPv4 address | name, ipv4 |
| **AAAA** | IPv6 address | name, ipv6 |
| **MX** | Mail exchange | name, priority, mailserver |
| **CNAME** | Canonical name | name, target |
| **TXT** | Text record | name, text |
| **SRV** | Service record | name, priority, weight, port, target |
| **PTR** | Pointer record | ip_octet, fqdn |
| **NS** | Name server | name, nameserver |
| **SOA** | Start of authority | *View only - auto-managed* |

### Service Management

```bash
# View status
systemctl status dns-manager

# View logs
journalctl -u dns-manager -f

# Restart service
systemctl restart dns-manager

# Stop service
systemctl stop dns-manager
```

### MongoDB Management

```bash
# View container status
docker-compose ps

# View MongoDB logs
docker-compose logs -f mongodb

# Restart MongoDB
docker-compose restart mongodb

# Stop MongoDB
docker-compose stop
```

## API Documentation

### Authentication Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Verify token

### Zone Endpoints

- `GET /api/zones` - List all zones
- `GET /api/zones/<zone_file>/records` - Get zone records

### Record Endpoints

- `POST /api/zones/<zone_file>/records` - Add record
- `PUT /api/zones/<zone_file>/records` - Update record
- `DELETE /api/zones/<zone_file>/records` - Delete record

### Service Endpoints

- `POST /api/reload/<zone_name>` - Reload zone with retry logic
- `POST /api/restart` - Restart named service (admin only)

### Log Endpoints

- `GET /api/logs` - Get event logs with filters
- `GET /api/logs/zone/<zone>` - Get logs for specific zone

All API endpoints (except login) require JWT authentication via `Authorization: Bearer <token>` header.

## Security Considerations

🔒 **Important Security Notes**:

1. **Access Control**: The application runs on port 2020. Ensure it's only accessible from trusted networks (VPN/internal)
2. **HTTPS**: Consider placing behind nginx with SSL/TLS for production
3. **Firewall**: If you have a firewall, allow port 2020 only from trusted sources
4. **Credentials**: Keep `/var/passwords/dns-manager-credentials.txt` secure (chmod 600)
5. **Root Access**: The application runs as root to modify DNS files and restart services

## Troubleshooting

### Application won't start

```bash
# Check service status
systemctl status dns-manager

# View detailed logs
journalctl -u dns-manager -n 50

# Verify MongoDB is running
docker-compose ps
```

### Can't login

```bash
# Reset admin password
cd /root/ns1
source venv/bin/activate
python3 << EOF
from backend.models import User
User.create('admin', 'newpassword123', role='admin')
EOF
```

### Zone reload fails

- Verify `rndc` is working: `rndc status`
- Check zone file syntax: `named-checkzone ZONE /var/named/ZONEFILE`
- Review named logs: `journalctl -u named -f`

## File Structure

```
ns1/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── auth.py             # Authentication logic
│   ├── config.py           # Configuration management
│   ├── dns_parser.py       # Zone file parser
│   ├── dns_operations.py   # DNS CRUD operations
│   ├── models.py           # Database models
│   ├── requirements.txt    # Python dependencies
│   └── routes/             # API route handlers
├── frontend/
│   ├── index.html          # Main HTML page
│   ├── css/
│   │   └── style.css       # Premium dark theme CSS
│   └── js/
│       └── app.js          # Frontend JavaScript
├── docker-compose.yml      # MongoDB container config
├── init-mongo.js           # MongoDB initialization
├── setup.sh                # Automated setup script
├── dns-manager.service     # Systemd service template
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License.

## Support

For issues or questions:
- Review the troubleshooting section above
- Check application logs: `journalctl -u dns-manager -f`
- Check MongoDB logs: `docker-compose logs -f`
- Review event logs in the web interface

## Credits

Developed for LinuxHardened DNS infrastructure management.

---

**⚡ DNS Manager** - Modern DNS Management Made Simple
# ns1-frontend
