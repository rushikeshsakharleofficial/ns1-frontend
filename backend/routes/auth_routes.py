from flask import Blueprint, request, jsonify, g
from auth import login_user, logout_user, token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    result = login_user(data['username'], data['password'])
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 401


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """User logout endpoint"""
    username = g.user['username']
    result = logout_user(username)
    return jsonify(result), 200


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify():
    """Verify token validity"""
    return jsonify({
        'success': True,
        'user': {
            'username': g.user['username'],
            'role': g.user['role']
        }
    }), 200
