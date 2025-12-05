import os
import subprocess
import time
from dns_parser import DNSParser
from config import config
from models import EventLog


class DNSOperations:
    """DNS operations including CRUD and service management"""
    
    @staticmethod
    def list_zones():
        """List all available DNS zones"""
        zones = []
        
        if not os.path.exists(config.NAMED_ZONE_DIR):
            return {'success': False, 'error': 'Zone directory not found'}
        
        try:
            for filename in os.listdir(config.NAMED_ZONE_DIR):
                file_path = os.path.join(config.NAMED_ZONE_DIR, filename)
                
                # Skip directories and system files
                if not os.path.isfile(file_path):
                    continue
                
                # Identify zone files by extension
                if filename.endswith(config.FORWARD_ZONE_PATTERN):
                    zone_name = filename.replace(config.FORWARD_ZONE_PATTERN, '')
                    zones.append({
                        'name': zone_name,
                        'type': 'forward',
                        'file': filename,
                        'path': file_path
                    })
                elif filename.endswith(config.REVERSE_ZONE_PATTERN):
                    zone_name = filename.replace(config.REVERSE_ZONE_PATTERN, '')
                    zones.append({
                        'name': zone_name,
                        'type': 'reverse',
                        'file': filename,
                        'path': file_path
                    })
            
            return {'success': True, 'zones': zones}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_zone_records(zone_file):
        """Get all records from a zone file"""
        zone_path = os.path.join(config.NAMED_ZONE_DIR, zone_file)
        
        try:
            parser = DNSParser(zone_path)
            data = parser.parse()
            return {'success': True, 'data': data}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def add_record(zone_file, record, username):
        """Add a new DNS record to a zone"""
        zone_path = os.path.join(config.NAMED_ZONE_DIR, zone_file)
        
        try:
            # Parse existing zone
            parser = DNSParser(zone_path)
            data = parser.parse()
            
            # Add new record
            data['records'].append(record)
            
            # Check if SOA exists
            if not data.get('soa'):
                return {'success': False, 'error': 'SOA record not found in zone file. Cannot update serial.'}
            
            # Increment serial number
            new_serial = DNSParser.increment_serial(data['soa']['serial'])
            data['soa']['serial'] = new_serial
            
            # Write updated zone file
            parser.write_zone_file(zone_path, data['ttl'], data['soa'], data['records'])
            
            # Log event
            EventLog.create(
                user=username,
                action='add_record',
                status='success',
                zone=zone_file,
                record_type=record['type'],
                details=record
            )
            
            return {'success': True, 'serial': new_serial}
        
        except Exception as e:
            # Log failure
            EventLog.create(
                user=username,
                action='add_record',
                status='failure',
                zone=zone_file,
                record_type=record.get('type', 'unknown'),
                error_message=str(e)
            )
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def update_record(zone_file, old_record, new_record, username):
        """Update an existing DNS record"""
        zone_path = os.path.join(config.NAMED_ZONE_DIR, zone_file)
        
        try:
            # Parse existing zone
            parser = DNSParser(zone_path)
            data = parser.parse()
            
            # Find and update the record
            record_found = False
            for i, rec in enumerate(data['records']):
                if DNSOperations._records_match(rec, old_record):
                    data['records'][i] = new_record
                    record_found = True
                    break
            
            if not record_found:
                return {'success': False, 'error': 'Record not found'}
            
            # Check if SOA exists
            if not data.get('soa'):
                return {'success': False, 'error': 'SOA record not found in zone file. Cannot update serial.'}
            
            # Increment serial number
            new_serial = DNSParser.increment_serial(data['soa']['serial'])
            data['soa']['serial'] = new_serial
            
            # Write updated zone file
            parser.write_zone_file(zone_path, data['ttl'], data['soa'], data['records'])
            
            # Log event
            EventLog.create(
                user=username,
                action='update_record',
                status='success',
                zone=zone_file,
                record_type=new_record['type'],
                details={'old': old_record, 'new': new_record}
            )
            
            return {'success': True, 'serial': new_serial}
        
        except Exception as e:
            EventLog.create(
                user=username,
                action='update_record',
                status='failure',
                zone=zone_file,
                error_message=str(e)
            )
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_record(zone_file, record, username):
        """Delete a DNS record from a zone"""
        zone_path = os.path.join(config.NAMED_ZONE_DIR, zone_file)
        
        try:
            # Parse existing zone
            parser = DNSParser(zone_path)
            data = parser.parse()
            
            # Find and remove the record
            initial_count = len(data['records'])
            data['records'] = [r for r in data['records'] if not DNSOperations._records_match(r, record)]
            
            if len(data['records']) == initial_count:
                return {'success': False, 'error': 'Record not found'}
            
            # Check if SOA exists
            if not data.get('soa'):
                return {'success': False, 'error': 'SOA record not found in zone file. Cannot update serial.'}
            
            # Increment serial number
            new_serial = DNSParser.increment_serial(data['soa']['serial'])
            data['soa']['serial'] = new_serial
            
            # Write updated zone file
            parser.write_zone_file(zone_path, data['ttl'], data['soa'], data['records'])
            
            # Log event
            EventLog.create(
                user=username,
                action='delete_record',
                status='success',
                zone=zone_file,
                record_type=record['type'],
                details=record
            )
            
            return {'success': True, 'serial': new_serial}
        
        except Exception as e:
            EventLog.create(
                user=username,
                action='delete_record',
                status='failure',
                zone=zone_file,
                error_message=str(e)
            )
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _records_match(record1, record2):
        """Check if two records match (for finding/updating)"""
        if record1['type'] != record2['type']:
            return False
        
        # Compare all fields except type
        for key in record1:
            if key != 'type' and record1.get(key) != record2.get(key):
                return False
        
        return True
    
    @staticmethod
    def reload_zone(zone_name, username):
        """Reload a specific zone using rndc with retry logic"""
        max_attempts = config.MAX_RELOAD_ATTEMPTS
        
        for attempt in range(1, max_attempts + 1):
            try:
                result = subprocess.run(
                    [config.RNDC_PATH, 'reload', zone_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # Check if reload was successful
                if 'zone reload up-to-date' in result.stdout or 'zone reload queued' in result.stdout:
                    EventLog.create(
                        user=username,
                        action='reload_zone',
                        status='success',
                        zone=zone_name,
                        details={'attempt': attempt, 'output': result.stdout}
                    )
                    return {
                        'success': True,
                        'attempt': attempt,
                        'message': 'Zone reloaded successfully',
                        'output': result.stdout
                    }
                
                # If not successful and not last attempt, wait before retry
                if attempt < max_attempts:
                    time.sleep(1)
            
            except subprocess.TimeoutExpired:
                if attempt < max_attempts:
                    time.sleep(1)
                    continue
            
            except Exception as e:
                EventLog.create(
                    user=username,
                    action='reload_zone',
                    status='failure',
                    zone=zone_name,
                    error_message=str(e)
                )
                return {'success': False, 'error': str(e)}
        
        # All attempts failed
        error_msg = f'Failed to reload zone after {max_attempts} attempts'
        EventLog.create(
            user=username,
            action='reload_zone',
            status='failure',
            zone=zone_name,
            error_message=error_msg
        )
        return {'success': False, 'error': error_msg, 'attempts': max_attempts}
    
    @staticmethod
    def restart_named_service(username):
        """Restart the named service using systemctl"""
        try:
            result = subprocess.run(
                [config.SYSTEMCTL_PATH, 'restart', 'named'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                EventLog.create(
                    user=username,
                    action='restart_service',
                    status='success',
                    details={'output': result.stdout}
                )
                return {'success': True, 'message': 'Named service restarted successfully'}
            else:
                error_msg = result.stderr or 'Failed to restart named service'
                EventLog.create(
                    user=username,
                    action='restart_service',
                    status='failure',
                    error_message=error_msg
                )
                return {'success': False, 'error': error_msg}
        
        except Exception as e:
            EventLog.create(
                user=username,
                action='restart_service',
                status='failure',
                error_message=str(e)
            )
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def validate_record(record):
        """Validate a DNS record before adding/updating"""
        rtype = record.get('type')
        
        if rtype not in config.SUPPORTED_RECORD_TYPES:
            return {'valid': False, 'error': f'Unsupported record type: {rtype}'}
        
        # Type-specific validation (simplified for brevity, matching existing code)
        if rtype == 'A':
            if 'name' not in record or 'ipv4' not in record:
                return {'valid': False, 'error': 'A record requires name and ipv4'}
            import re
            if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', record['ipv4']):
                return {'valid': False, 'error': 'Invalid IPv4 address format'}
        
        return {'valid': True}

    @staticmethod
    def sync_slave(zone_name, username):
        """Sync zone to slave by deleting file and restarting slave named"""
        if not config.NS2_HOST:
            return None # Not configured
            
        try:
            # Determine filename
            # This is a bit of a guess since we only have zone_name. 
            # We try to match what's in our local directory to find the extension.
            # But simplest is to construct it based on patterns if we can.
            
            filename = None
            forward_path = os.path.join(config.NAMED_ZONE_DIR, f"{zone_name}{config.FORWARD_ZONE_PATTERN}")
            reverse_path = os.path.join(config.NAMED_ZONE_DIR, f"{zone_name}{config.REVERSE_ZONE_PATTERN}")
            
            if os.path.exists(forward_path):
                filename = f"{zone_name}{config.FORWARD_ZONE_PATTERN}"
            elif os.path.exists(reverse_path):
                filename = f"{zone_name}{config.REVERSE_ZONE_PATTERN}"
            else:
                # If cannot find local file, maybe it has a different naming check or custom
                # Fallback: assume forward pattern if not found?
                # Or just return error
                 return {'success': False, 'error': f'Could not determine filename for zone {zone_name}'}
            
            slave_file_path = os.path.join(config.NS2_SLAVE_DIR, filename)
            
            # Construct SSH command
            # rm -f /var/named/slaves/filename && systemctl restart named
            cmd = f"ssh {config.NS2_USER}@{config.NS2_HOST} 'rm -f {slave_file_path} && systemctl restart named'"
            
            # Execute
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0:
                EventLog.create(
                    user=username,
                    action='sync_slave',
                    status='success',
                    details={'zone': zone_name, 'host': config.NS2_HOST}
                )
                return {'success': True}
            else:
                EventLog.create(
                    user=username,
                    action='sync_slave',
                    status='failure',
                    details={'error': result.stderr}
                )
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def create_zone(zone_name, zone_type, username, allow_transfer=None, also_notify=None):
        """Create a new zone file with basic template"""
        # Validate zone name (basic)
        if not zone_name or ' ' in zone_name:
            return {'success': False, 'error': 'Invalid zone name'}

        # Determine filename
        if zone_type == 'forward':
            filename = f"{zone_name}{config.FORWARD_ZONE_PATTERN}"
        elif zone_type == 'reverse':
            filename = f"{zone_name}{config.REVERSE_ZONE_PATTERN}"
        else:
            return {'success': False, 'error': 'Invalid zone type'}
            
        file_path = os.path.join(config.NAMED_ZONE_DIR, filename)
        
        if os.path.exists(file_path):
            return {'success': False, 'error': f'Zone file {filename} already exists'}
            
        try:
            # Basic Template
            # We need valid SOA and NS to be valid
            # Default TTL
            
            serial = time.strftime('%Y%m%d%H')
            
            content = f"""$TTL 86400
@   IN  SOA ns1.{zone_name}. admin.{zone_name}. (
        {serial}  ; Serial
        3600        ; Refresh
        1800        ; Retry
        604800      ; Expire
        86400 )     ; Minimum TTL

; Name Servers
@   IN  NS  ns1.{zone_name}.
@   IN  NS  ns2.{zone_name}.

; A Records
ns1 IN  A   127.0.0.1
ns2 IN  A   127.0.0.1
@   IN  A   127.0.0.1
"""
            with open(file_path, 'w') as f:
                f.write(content)
                
            # Set ownership to named:named
            try:
                # Get UID/GID for 'named' user (or root if not found/mocking)
                # In standard setup, 'named' exists.
                # If running as root, we can chown.
                import pwd
                import grp
                uid = pwd.getpwnam('named').pw_uid
                gid = grp.getgrnam('named').gr_gid
                os.chown(file_path, uid, gid)
            except Exception as e:
                # Log warning but don't fail, might be permission or dev env
                print(f"Warning: Could not set owner to named: {e}")
            
            # Use provided IPs or Defaults
            # Parse from string if provided (semicolon separated in UI, but we expect cleaner input logic?)
            # UI sends raw string like "1.2.3.4; 5.6.7.8"
            
            def parse_ips(ip_str, defaults):
                if not ip_str: 
                    return defaults
                # Clean up: split by semicolon, strip whitespace, remove empty
                return [ip.strip() for ip in ip_str.replace('\n', ';').split(';') if ip.strip()]

            transfer_list = parse_ips(allow_transfer, config.DEFAULT_ALLOW_TRANSFER)
            notify_list = parse_ips(also_notify, config.DEFAULT_ALSO_NOTIFY)
            
            allow_transfer_str = ';\n        '.join(transfer_list)
            also_notify_str = ';\n        '.join(notify_list)
            
            # Format the entry
            # Ensure proper indentation
            conf_entry = f"""
zone "{zone_name}" IN {{
    type master;
    file "{filename}";
    allow-update {{ none; }};
    allow-transfer {{
        {allow_transfer_str};
    }};
    also-notify {{
        {also_notify_str};
    }};
}};
"""
            
            # Check if zone already in named.conf (simple string check)
            # A strict parser check would be better but expensive/complex to implement safely
            try:
                with open(config.NAMED_CONF_PATH, 'r') as f:
                    current_conf = f.read()
                
                if f'zone "{zone_name}"' in current_conf:
                    # Already exists in conf, maybe commented out or previous attempt?
                    pass
                else:
                    with open(config.NAMED_CONF_PATH, 'a') as f:
                        f.write(conf_entry)
                        
                    # Reload configuration to pick up new zone
                    subprocess.run([config.RNDC_PATH, 'reconfig'], check=False)
                    
            except Exception as e:
                # Partial failure (file created, conf failed)
                return {'success': True, 'warning': f'File created but named.conf update failed: {str(e)}', 'file': filename}

            EventLog.create(user=username, action='create_zone', status='success', zone=zone_name)
            return {'success': True, 'message': f'Zone {zone_name} created and added to named.conf', 'file': filename}

        except Exception as e:
            EventLog.create(user=username, action='create_zone', status='failure', error_message=str(e))
            return {'success': False, 'error': str(e)}
