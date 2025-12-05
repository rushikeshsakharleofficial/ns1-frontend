from flask import Blueprint, request, jsonify, g
from auth import admin_required
from models import User, EventLog
import re

user_bp = Blueprint('users', __name__)

@user_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """List all users"""
    try:
        users = User.list_all()
        # Ensure proper ID conversion if needed, though list_all handles basics
        formatted_users = []
        for user in users:
            formatted_users.append({
                'username': user['username'],
                'role': user['role'],
                'created_at': user.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if user.get('created_at') else None,
                'last_login': user.get('last_login').strftime('%Y-%m-%d %H:%M:%S') if user.get('last_login') else None
            })
            
        return jsonify({
            'success': True,
            'users': formatted_users
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@user_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
    username = data['username']
    password = data['password']
    role = data.get('role', 'user')
    
    # Validation
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        return jsonify({'success': False, 'error': 'Username must be 3-20 alphanumeric characters'}), 400
        
    if len(password) < 8:
        return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
    # Check if user exists
    if User.find_by_username(username):
        return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
    result = User.create(username, password, role)
    
    if result['success']:
        EventLog.create(
            user=g.user['username'],
            action='create_user',
            status='success',
            details={'target_user': username, 'role': role}
        )
        return jsonify({'success': True, 'message': 'User created successfully'}), 201
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Failed to create user')}), 500


@user_bp.route('/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """Delete a user"""
    if username == 'admin':
        return jsonify({'success': False, 'error': 'Cannot delete the main admin user'}), 403
        
    if username == g.user['username']:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 403
        
    if User.delete(username):
        EventLog.create(
            user=g.user['username'],
            action='delete_user',
            status='success',
            details={'target_user': username}
        )
        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    else:
        return jsonify({'success': False, 'error': 'User not found'}), 404
