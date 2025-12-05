from flask import Blueprint, jsonify
from auth import token_required
from config import config
from named_conf_parser import NamedConfParser
from dns_parser import DNSParser
import os

zone_bp = Blueprint('zones', __name__)

@zone_bp.route('/zones', methods=['GET'])
@token_required
def get_zones():
    """Get all zones from named.conf"""
    try:
        parser = NamedConfParser()
        all_zones = parser.parse()
        
        # Filter to only master zones and exclude special zones
        zones = []
        for zone in all_zones:
            if zone['type'] == 'master' and zone['zone_type'] != 'special':
                # Verify zone file exists
                if zone['file'] and os.path.exists(zone['file']):
                    zones.append({
                        'name': zone['name'],
                        'type': zone['zone_type'],
                        'file': zone['file_basename'],
                        'full_path': zone['file']
                    })
        
        return jsonify({
            'success': True,
            'zones': zones
        })
    
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'error': f'Configuration file not found: {str(e)}'
        }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@zone_bp.route('/zones/<zone_file>/records', methods=['GET'])
@token_required
def get_zone_records(zone_file):
    """Get all records for a specific zone"""
    try:
        # Parse named.conf to get zones
        parser = NamedConfParser()
        parser.parse()
        
        # Find the zone by file basename
        zone_info = None
        for zone in parser.zones:
            if zone.get('file_basename') == zone_file:
                zone_info = zone
                break
        
        if not zone_info:
            return jsonify({
                'success': False,
                'error': f'Zone file {zone_file} not found in named.conf'
            }), 404
        
        zone_file_path = zone_info['file']
        
        if not os.path.exists(zone_file_path):
            return jsonify({
                'success': False,
                'error': f'Zone file does not exist: {zone_file_path}'
            }), 404
        
        # Parse the zone file
        dns_parser = DNSParser(zone_file_path)
        zone_data = dns_parser.parse()
        
        return jsonify({
            'success': True,
            'data': zone_data
        })
    
        return jsonify({
            'success': True,
            'data': zone_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@zone_bp.route('/zones', methods=['POST'])
@token_required
def create_zone():
    """Create a new zone file"""
    try:
        from flask import request, g
        from dns_operations import DNSOperations
        
        data = request.json
        if not data or 'name' not in data or 'type' not in data:
            return jsonify({'success': False, 'error': 'Missing name or type'}), 400
            
        allow_transfer = data.get('allow_transfer_ips')
        also_notify = data.get('also_notify_ips')
        
        result = DNSOperations.create_zone(data['name'], data['type'], g.user['username'], allow_transfer, also_notify)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
