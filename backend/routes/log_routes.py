from flask import Blueprint, request, jsonify
from bson import ObjectId
from auth import token_required
from models import EventLog

log_bp = Blueprint('log', __name__)


@log_bp.route('/logs', methods=['GET'])
@token_required
def get_logs():
    """Get event logs with optional filters"""
    # Get query parameters
    limit = request.args.get('limit', 100, type=int)
    user_filter = request.args.get('user', None)
    action_filter = request.args.get('action', None)
    
    # Limit maximum to 500
    limit = min(limit, 500)
    
    # Fetch logs
    logs = EventLog.find_recent(limit=limit, user=user_filter, action=action_filter)
    
    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log['_id'] = str(log['_id'])
        # Convert datetime to ISO format string
        if 'timestamp' in log:
            log['timestamp'] = log['timestamp'].isoformat() + 'Z'
    
    return jsonify({
        'success': True,
        'logs': logs,
        'count': len(logs)
    }), 200


@log_bp.route('/logs/zone/<zone>', methods=['GET'])
@token_required
def get_zone_logs(zone):
    """Get event logs for a specific zone"""
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 200)
    
    logs = EventLog.find_by_zone(zone, limit=limit)
    
    # Convert ObjectId to string for JSON serialization
    for log in logs:
        log['_id'] = str(log['_id'])
        if 'timestamp' in log:
            log['timestamp'] = log['timestamp'].isoformat() + 'Z'
    
    return jsonify({
        'success': True,
        'logs': logs,
        'count': len(logs)
    }), 200
