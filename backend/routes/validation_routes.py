from flask import Blueprint, jsonify, request
from auth import token_required, admin_required
from config import config
import subprocess
import os

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/validate/config', methods=['POST'])
@admin_required
def validate_config():
    """Validate named.conf syntax using named-checkconf"""
    try:
        result = subprocess.run(
            [config.NAMED_CHECKCONF_PATH or '/usr/sbin/named-checkconf', config.NAMED_CONF_PATH],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'valid': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
            'message': 'Configuration is valid' if result.returncode == 0 else 'Configuration has errors'
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Validation timed out'
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@validation_bp.route('/validate/zone/<zone_name>', methods=['POST'])
@admin_required
def validate_zone(zone_name):
    """Validate zone file syntax using named-checkzone"""
    try:
        from named_conf_parser import NamedConfParser
        
        # Get zone file path from named.conf
        parser = NamedConfParser()
        parser.parse()
        zone_info = parser.get_zone_by_name(zone_name)
        
        if not zone_info:
            return jsonify({
                'success': False,
                'error': f'Zone {zone_name} not found in named.conf'
            }), 404
        
        zone_file = zone_info['file']
        
        if not os.path.exists(zone_file):
            return jsonify({
                'success': False,
                'error': f'Zone file not found: {zone_file}'
            }), 404
        
        result = subprocess.run(
            [config.NAMED_CHECKZONE_PATH or '/usr/sbin/named-checkzone', zone_name, zone_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return jsonify({
            'success': result.returncode == 0,
            'valid': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
            'message': f'Zone {zone_name} is valid' if result.returncode == 0 else f'Zone {zone_name} has errors'
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Validation timed out'
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
