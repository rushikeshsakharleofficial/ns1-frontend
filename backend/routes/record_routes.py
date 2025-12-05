from flask import Blueprint, request, jsonify, g
from auth import token_required
from dns_operations import DNSOperations

record_bp = Blueprint('record', __name__)


@record_bp.route('/zones/<zone_file>/records', methods=['POST'])
@token_required
def add_record(zone_file):
    """Add a new DNS record to a zone"""
    data = request.get_json()
    
    if not data or 'record' not in data:
        return jsonify({'success': False, 'error': 'Record data required'}), 400
    
    record = data['record']
    username = g.user['username']
    
    # Validate record
    validation = DNSOperations.validate_record(record)
    if not validation['valid']:
        return jsonify({'success': False, 'error': validation['error']}), 400
    
    # Add record
    result = DNSOperations.add_record(zone_file, record, username)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@record_bp.route('/zones/<zone_file>/records', methods=['PUT'])
@token_required
def update_record(zone_file):
    """Update an existing DNS record"""
    data = request.get_json()
    
    if not data or 'old_record' not in data or 'new_record' not in data:
        return jsonify({'success': False, 'error': 'Both old_record and new_record required'}), 400
    
    old_record = data['old_record']
    new_record = data['new_record']
    username = g.user['username']
    
    # Validate new record
    validation = DNSOperations.validate_record(new_record)
    if not validation['valid']:
        return jsonify({'success': False, 'error': validation['error']}), 400
    
    # Update record
    result = DNSOperations.update_record(zone_file, old_record, new_record, username)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@record_bp.route('/zones/<zone_file>/records', methods=['DELETE'])
@token_required
def delete_record(zone_file):
    """Delete a DNS record from a zone"""
    data = request.get_json()
    
    if not data or 'record' not in data:
        return jsonify({'success': False, 'error': 'Record data required'}), 400
    
    record = data['record']
    username = g.user['username']
    
    # Delete record
    result = DNSOperations.delete_record(zone_file, record, username)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500
