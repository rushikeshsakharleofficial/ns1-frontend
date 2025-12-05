import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from config import config
from models import User, EventLog


def generate_token(username, role):
    """Generate JWT token for authenticated user"""
    payload = {
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=config.JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')
    return token


def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return {'valid': True, 'payload': payload}
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'valid': False, 'error': 'Invalid token'}


def token_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'success': False, 'error': 'Authentication token is missing'}), 401
        
        # Verify token
        result = verify_token(token)
        if not result['valid']:
            return jsonify({'success': False, 'error': result['error']}), 401
        
        # Add user info to global request context
        g.user = result['payload']
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """Decorator to protect routes that require admin role"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.user.get('role') != 'admin':
            return jsonify({'success': False, 'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated


def login_user(username, password):
    """Authenticate user and return token"""
    # Verify credentials
    if not User.verify_password(username, password):
        EventLog.create(
            user=username,
            action='login',
            status='failure',
            error_message='Invalid credentials'
        )
        return {'success': False, 'error': 'Invalid username or password'}
    
    # Get user details
    user = User.find_by_username(username)
    if not user:
        return {'success': False, 'error': 'User not found'}
    
    # Update last login
    User.update_last_login(username)
    
    # Generate token
    token = generate_token(username, user['role'])
    
    # Log successful login
    EventLog.create(
        user=username,
        action='login',
        status='success'
    )
    
    return {
        'success': True,
        'token': token,
        'user': {
            'username': username,
            'role': user['role']
        }
    }


def logout_user(username):
    """Log user logout event"""
    EventLog.create(
        user=username,
        action='logout',
        status='success'
    )
    return {'success': True, 'message': 'Logged out successfully'}
