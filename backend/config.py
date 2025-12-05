import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Load environment variables from .env file
# Try current dir and parent dir
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    """Application configuration"""
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 2020))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://dnsadmin:ChangeMeInProduction123!@localhost:27017/dns_manager?authSource=admin')
    
    # DNS Configuration
    NAMED_ZONE_DIR = os.getenv('NAMED_ZONE_DIR', '/var/named')
    NAMED_CONF_PATH = os.getenv('NAMED_CONF_PATH', '/etc/named.conf')
    RNDC_PATH = os.getenv('RNDC_PATH', '/usr/sbin/rndc')
    SYSTEMCTL_PATH = os.getenv('SYSTEMCTL_PATH', '/usr/bin/systemctl')
    NAMED_CHECKCONF_PATH = os.getenv('NAMED_CHECKCONF_PATH', '/usr/sbin/named-checkconf')
    NAMED_CHECKZONE_PATH = os.getenv('NAMED_CHECKZONE_PATH', '/usr/sbin/named-checkzone')
    MAX_RELOAD_ATTEMPTS = int(os.getenv('MAX_RELOAD_ATTEMPTS', 5))
    
    # Zone file patterns
    FORWARD_ZONE_PATTERN = '.hosts'
    REVERSE_ZONE_PATTERN = '.rev'

    # Supported DNS record types
    SUPPORTED_RECORD_TYPES = ['A', 'AAAA', 'MX', 'TXT', 'SRV', 'CNAME', 'PTR', 'NS', 'SOA']
    
    # Default Admin Credentials (only used during initial setup)
    DEFAULT_ADMIN_USERNAME = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.getenv('DEFAULT_ADMIN_PASSWORD', '')

    # Slave Server Configuration
    # Comma-separated list of IPs/Hostnames, e.g., "192.168.1.5,192.168.1.6"
    SLAVE_SERVERS = os.getenv('SLAVE_SERVERS', '').split(',')
    SLAVE_SERVERS = [s.strip() for s in SLAVE_SERVERS if s.strip()]
    
    SLAVE_USER = os.getenv('SLAVE_USER', 'root')
    SLAVE_SSH_PORT = os.getenv('SLAVE_SSH_PORT', '15000')
    SLAVE_API_PORT = int(os.getenv('SLAVE_API_PORT', 5000))
    SLAVE_SECRET = os.getenv('SLAVE_SECRET', 'changeme')
    SLAVE_DIR = os.getenv('SLAVE_DIR', '/var/named/slaves')

    # Zone Default Allow List (Linode Slaves)
    DEFAULT_ALLOW_TRANSFER = [
        "104.237.137.10", "45.79.109.10", "74.207.225.10", "143.42.7.10",
        "207.192.70.10", "109.74.194.10", "172.237.44.232",
        "2600:3c00::a", "2600:3c01::a", "2600:3c02::a", "2600:3c03::a", "2a01:7e00::a"
    ]
    
    DEFAULT_ALSO_NOTIFY = [
        "104.237.137.10", "45.79.109.10", "74.207.225.10", "143.42.7.10",
        "207.192.70.10", "172.237.44.232"
    ]

config = Config()
