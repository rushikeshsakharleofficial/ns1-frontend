from flask import Blueprint, request, jsonify, g
from auth import token_required, admin_required
from dns_operations import DNSOperations

service_bp = Blueprint('service', __name__)


@service_bp.route('/reload/<zone_name>', methods=['POST'])
@token_required
def reload_zone(zone_name):
    """Reload a specific DNS zone using rndc"""
    username = g.user['username']
    
    result = DNSOperations.reload_zone(zone_name, username)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@service_bp.route('/restart', methods=['POST'])
@admin_required
def restart_named():
    """Restart the named service (admin only)"""
    username = g.user['username']
    
    result = DNSOperations.restart_named_service(username)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500
