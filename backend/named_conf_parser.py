import re
import os
from config import config


class NamedConfParser:
    """Parser for BIND named.conf configuration file"""
    
    def __init__(self, conf_path=None):
        self.conf_path = conf_path or config.NAMED_CONF_PATH
        self.zones = []
    
    def parse(self):
        """Parse named.conf and extract zone definitions"""
        if not os.path.exists(self.conf_path):
            raise FileNotFoundError(f"named.conf not found: {self.conf_path}")
        
        with open(self.conf_path, 'r') as f:
            content = f.read()
        
        # Remove C-style comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        
        self.zones = []
        
        # Match zone blocks: zone "name" { ... }
        zone_pattern = r'zone\s+"([^"]+)"\s+(?:IN\s+)?\{([^}]+)\}'
        
        for match in re.finditer(zone_pattern, content, re.DOTALL | re.MULTILINE):
            zone_name = match.group(1)
            zone_block = match.group(2)
            
            # Extract zone properties
            zone_info = self._parse_zone_block(zone_name, zone_block)
            
            # Only include master zones
            if zone_info and zone_info.get('type') == 'master':
                self.zones.append(zone_info)
        
        return self.zones
    
    def _parse_zone_block(self, zone_name, zone_block):
        """Parse individual zone block content"""
        zone_info = {
            'name': zone_name,
            'type': None,
            'file': None,
            'allow_update': [],
            'allow_transfer': []
        }
        
        # Extract type
        type_match = re.search(r'type\s+(\w+)\s*;', zone_block)
        if type_match:
            zone_info['type'] = type_match.group(1)
        
        # Extract file path
        file_match = re.search(r'file\s+"([^"]+)"\s*;', zone_block)
        if file_match:
            file_path = file_match.group(1)
            # Handle relative paths
            if not file_path.startswith('/'):
                file_path = os.path.join(config.NAMED_ZONE_DIR, file_path)
            zone_info['file'] = file_path
        
        # Extract allow-update
        update_match = re.search(r'allow-update\s+\{([^}]+)\}', zone_block)
        if update_match:
            zone_info['allow_update'] = [
                item.strip().rstrip(';') 
                for item in update_match.group(1).split() 
                if item.strip() and item.strip() != 'none'
            ]
        
        # Extract allow-transfer
        transfer_match = re.search(r'allow-transfer\s+\{([^}]+)\}', zone_block)
        if transfer_match:
            zone_info['allow_transfer'] = [
                item.strip().rstrip(';') 
                for item in transfer_match.group(1).split() 
                if item.strip() and item.strip() != 'none'
            ]
        
        # Determine zone category (forward/reverse)
        zone_info['zone_type'] = self._determine_zone_type(zone_name)
        
        # Extract just the filename from full path for display
        if zone_info['file']:
            zone_info['file_basename'] = os.path.basename(zone_info['file'])
        
        return zone_info
    
    def _determine_zone_type(self, zone_name):
        """Determine if zone is forward or reverse based on name"""
        # Reverse zones
        if zone_name.endswith('.in-addr.arpa') or zone_name.endswith('.ip6.arpa'):
            return 'reverse'
        # Special zones
        if zone_name in ['localhost', '0.0.127.in-addr.arpa', '1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa']:
            return 'special'
        # Forward zones
        return 'forward'
    
    def get_master_zones(self):
        """Get only master zones (exclude slaves, hints, etc.)"""
        return [zone for zone in self.zones if zone.get('type') == 'master']
    
    def get_zone_by_name(self, zone_name):
        """Get zone info by name"""
        for zone in self.zones:
            if zone['name'] == zone_name:
                return zone
        return None
    
    def add_zone_entry(self, zone_name, zone_file, zone_type='master'):
        """Add a new zone entry to named.conf"""
        zone_block = f'''
zone "{zone_name}" {{
    type {zone_type};
    file "{zone_file}";
    allow-update {{ none; }};
}};
'''
        
        # Read current config
        with open(self.conf_path, 'r') as f:
            content = f.read()
        
        # Check if zone already exists
        if f'zone "{zone_name}"' in content:
            raise ValueError(f"Zone {zone_name} already exists in named.conf")
        
        # Backup original config
        backup_path = f"{self.conf_path}.backup"
        with open(backup_path, 'w') as f:
            f.write(content)
        
        # Append new zone block
        with open(self.conf_path, 'a') as f:
            f.write(zone_block)
        
        return True
