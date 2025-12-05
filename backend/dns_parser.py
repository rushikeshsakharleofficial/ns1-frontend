import re
import os
from datetime import datetime
from config import config


class DNSParser:
    """Parser for BIND DNS zone files"""
    
    def __init__(self, zone_file_path):
        self.zone_file_path = zone_file_path
        self.records = []
        self.soa = None
        self.ttl = None
    
    def parse(self):
        """Parse the zone file and extract all records"""
        if not os.path.exists(self.zone_file_path):
            raise FileNotFoundError(f"Zone file not found: {self.zone_file_path}")
        
        with open(self.zone_file_path, 'r') as f:
            content = f.read()
        
        self.records = []
        self.soa = None
        self.ttl = None
        
        # Extract TTL
        ttl_match = re.search(r'^\$TTL\s+(\d+)', content, re.MULTILINE)
        if ttl_match:
            self.ttl = ttl_match.group(1)
        
        # Extract SOA record - Try strict pattern first (with comments), then loose pattern
        soa_pattern_strict = r'@\s+IN\s+SOA\s+(\S+)\s+(\S+)\s+\(\s*(\d+)\s*;\s*Serial.*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?\)'
        soa_pattern_loose = r'@\s+IN\s+SOA\s+(\S+)\s+(\S+)\s+\(\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*\)'
        
        # Normalize content to handle newlines within parentheses easier
        content_normalized = content
        
        match = re.search(soa_pattern_strict, content, re.DOTALL | re.IGNORECASE)
        if not match:
             # Try loose pattern (without relying on comments)
            match = re.search(soa_pattern_loose, content, re.DOTALL | re.IGNORECASE)
            
        if match:
            self.soa = {
                'type': 'SOA',
                'primary_ns': match.group(1),
                'admin_email': match.group(2),
                'serial': match.group(3),
                'refresh': match.group(4),
                'retry': match.group(5),
                'expire': match.group(6),
                'minimum': match.group(7)
            }
        
        # Parse different record types
        self._parse_ns_records(content)
        self._parse_a_records(content)
        self._parse_aaaa_records(content)
        self._parse_mx_records(content)
        self._parse_txt_records(content)
        self._parse_srv_records(content)
        self._parse_cname_records(content)
        self._parse_ptr_records(content)
        
        return {
            'ttl': self.ttl,
            'soa': self.soa,
            'records': self.records
        }
    
    
    def _extract_comment(self, line):
        """Extract inline comment from a record line"""
        # Find comment after the record data (anything after ;)
        if ';' in line:
            parts = line.split(';', 1)
            if len(parts) > 1:
                return parts[1].strip()
        return None
    
    def _parse_ns_records(self, content):
        """Parse NS records"""
        pattern = r'^(\S+)\s+IN\s+NS\s+(\S+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'NS',
                'name': match.group(1),
                'nameserver': match.group(2)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    def _parse_a_records(self, content):
        """Parse A records"""
        pattern = r'^(\S+)\s+IN\s+A\s+(\d+\.\d+\.\d+\.\d+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'A',
                'name': match.group(1),
                'ipv4': match.group(2)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    def _parse_aaaa_records(self, content):
        """Parse AAAA records"""
        pattern = r'^(\S+)\s+IN\s+AAAA\s+([0-9a-fA-F:]+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'AAAA',
                'name': match.group(1),
                'ipv6': match.group(2)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    def _parse_mx_records(self, content):
        """Parse MX records"""
        pattern = r'^(\S+)\s+IN\s+MX\s+(\d+)\s+(\S+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'MX',
                'name': match.group(1),
                'priority': int(match.group(2)),
                'mailserver': match.group(3)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    def _parse_txt_records(self, content):
        """Parse TXT records (including multi-line)"""
        # Single-line TXT
        pattern = r'^(\S+)\s+TXT\s+"([^"]+)"(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'TXT',
                'name': match.group(1),
                'text': match.group(2)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
        
        # Multi-line TXT (parentheses)
        multi_pattern = r'^(\S+)\s+IN\s+TXT\s+\((.*?)\)'
        for match in re.finditer(multi_pattern, content, re.DOTALL | re.MULTILINE):
            name = match.group(1)
            text_content = match.group(2)
            # Extract all quoted strings and join them
            text_parts = re.findall(r'"([^"]*)"', text_content)
            combined_text = ''.join(text_parts)
            self.records.append({
                'type': 'TXT',
                'name': name,
                'text': combined_text
            })
    
    def _parse_srv_records(self, content):
        """Parse SRV records"""
        pattern = r'^(\S+)\s+SRV\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'SRV',
                'name': match.group(1),
                'priority': int(match.group(2)),
                'weight': int(match.group(3)),
                'port': int(match.group(4)),
                'target': match.group(5)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    def _parse_cname_records(self, content):
        """Parse CNAME records"""
        pattern = r'^(\S+)\s+IN\s+CNAME\s+(\S+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'CNAME',
                'name': match.group(1),
                'target': match.group(2)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    def _parse_ptr_records(self, content):
        """Parse PTR records"""
        pattern = r'^(\d+)\s+IN\s+PTR\s+(\S+)(.*)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            record = {
                'type': 'PTR',
                'ip_octet': match.group(1),
                'fqdn': match.group(2)
            }
            comment = self._extract_comment(match.group(0))
            if comment:
                record['comment'] = comment
            self.records.append(record)
    
    @staticmethod
    def increment_serial(current_serial):
        """Increment serial number in YYYYMMDDHH format"""
        now = datetime.now()
        # Format: YYYYMMDDHH
        target_str = now.strftime('%Y%m%d%H')
        target_serial = int(target_str)
        
        try:
            current = int(current_serial)
            
            # If our time-based serial is greater, use it (jump forward)
            if target_serial > current:
                return str(target_serial)
            elif target_serial == current:
                # User preference: keep it current (don't increment just for uniqueness)
                # Since we use forced slave sync (delete/restart), we don't strictly need higher serials
                return str(target_serial)
            else:
                # If target is older than current (time moved back?), keep current
                # or increment if you wanted STRICT uniqueness, but user wants "current" logic
                return str(current)
        except (ValueError, TypeError):
            return str(target_serial)
    
    @staticmethod
    def format_record(record):
        """Format a record dictionary into zone file syntax"""
        rtype = record['type']
        comment_suffix = f" ; {record['comment']}" if record.get('comment') else ""
        
        if rtype == 'A':
            return f"{record['name']:<15} IN A {record['ipv4']}{comment_suffix}"
        
        elif rtype == 'AAAA':
            return f"{record['name']:<15} IN AAAA {record['ipv6']}{comment_suffix}"
        
        elif rtype == 'MX':
            return f"{record['name']:<15} IN MX {record['priority']} {record['mailserver']}{comment_suffix}"
        
        elif rtype == 'TXT':
            # Handle long TXT records (split if needed)
            text = record['text']
            if len(text) > 200:
                # Multi-line format
                parts = []
                for i in range(0, len(text), 200):
                    parts.append(f'  "{text[i:i+200]}"')
                return f"{record['name']} IN TXT (\n" + '\n'.join(parts) + "\n)"
            else:
                return f"{record['name']} TXT \"{text}\"{comment_suffix}"
        
        elif rtype == 'SRV':
            return f"{record['name']} SRV {record['priority']} {record['weight']} {record['port']} {record['target']}{comment_suffix}"
        
        elif rtype == 'CNAME':
            return f"{record['name']:<15} IN CNAME {record['target']}{comment_suffix}"
        
        elif rtype == 'PTR':
            return f"{record['ip_octet']:<15} IN PTR {record['fqdn']}{comment_suffix}"
        
        elif rtype == 'NS':
            return f"{record['name']} IN NS {record['nameserver']}{comment_suffix}"
        
        return ""
    
    def write_zone_file(self, output_path, ttl, soa, records):
        """Write zone file with updated records"""
        lines = []
        
        # Write TTL
        lines.append(f"$TTL {ttl}")
        
        # Write SOA
        lines.append(f"@   IN SOA  {soa['primary_ns']} {soa['admin_email']} (")
        lines.append(f"            {soa['serial']}")
        lines.append(f"            {soa['refresh']}")
        lines.append(f"            {soa['retry']}")
        lines.append(f"            {soa['expire']}")
        lines.append(f"            {soa['minimum']} )")
        lines.append("")
        
        # Group records by type
        record_groups = {}
        for record in records:
            rtype = record['type']
            if rtype not in record_groups:
                record_groups[rtype] = []
            record_groups[rtype].append(record)
        
        # Write records in organized sections
        type_order = ['NS', 'A', 'AAAA', 'MX', 'CNAME', 'TXT', 'SRV', 'PTR']
        
        for rtype in type_order:
            if rtype in record_groups:
                lines.append(f"; --- {rtype} Records ---")
                for record in record_groups[rtype]:
                    lines.append(self.format_record(record))
                lines.append("")
        
        # Write any remaining types not in the standard order
        for rtype, recs in record_groups.items():
            if rtype not in type_order:
                lines.append(f"; --- {rtype} Records ---")
                for record in recs:
                    lines.append(self.format_record(record))
                lines.append("")
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return True
