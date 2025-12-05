from pymongo import MongoClient
from datetime import datetime
import bcrypt
from config import config

# MongoDB connection
client = MongoClient(config.MONGO_URI)
db = client.dns_manager

# Collections
users_collection = db.users
event_logs_collection = db.event_logs


class User:
    @staticmethod
    def create_indexes():
        """Create database indexes"""
        try:
            users_collection.create_index('username', unique=True)
            return True
        except Exception as e:
            print(f"Index creation error: {e}")
            return False
    @staticmethod
    def create(username, password, role='user'):
        """Create a new user with hashed password"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            'username': username,
            'password_hash': password_hash.decode('utf-8'),
            'role': role,
            'created_at': datetime.utcnow()
        }
        
        try:
            result = users_collection.insert_one(user_data)
            return {'success': True, 'user_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        return users_collection.find_one({'username': username})
    
    @staticmethod
    def verify_password(username, password):
        """Verify user password"""
        user = User.find_by_username(username)
        if not user:
            return False
        
        stored_hash = user['password_hash'].encode('utf-8')
        password_bytes = password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, stored_hash)
    
    @staticmethod
    def update_last_login(username):
        """Update last login timestamp"""
        users_collection.update_one(
            {'username': username},
            {'$set': {'last_login': datetime.utcnow()}}
        )
    
    @staticmethod
    def list_all():
        """List all users (without password hashes)"""
        users = users_collection.find({}, {'password_hash': 0})
        return list(users)
    
    @staticmethod
    def delete(username):
        """Delete a user"""
        result = users_collection.delete_one({'username': username})
        return result.deleted_count > 0


class EventLog:
    """Event log model for audit trail"""
    
    @staticmethod
    def create(user, action, status, zone=None, record_type=None, details=None, error_message=None):
        """Create a new event log entry"""
        log_data = {
            'timestamp': datetime.utcnow(),
            'user': user,
            'action': action,
            'status': status
        }
        
        if zone:
            log_data['zone'] = zone
        if record_type:
            log_data['record_type'] = record_type
        if details:
            log_data['details'] = details
        if error_message:
            log_data['error_message'] = error_message
        
        try:
            result = event_logs_collection.insert_one(log_data)
            return {'success': True, 'log_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def find_recent(limit=100, user=None, action=None):
        """Find recent event logs with optional filters"""
        query = {}
        if user:
            query['user'] = user
        if action:
            query['action'] = action
        
        logs = event_logs_collection.find(query).sort('timestamp', -1).limit(limit)
        return list(logs)
    
    @staticmethod
    def find_by_zone(zone, limit=50):
        """Find event logs for a specific zone"""
        logs = event_logs_collection.find({'zone': zone}).sort('timestamp', -1).limit(limit)
        return list(logs)
    
    @staticmethod
    def delete_old(days=90):
        """Delete event logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = event_logs_collection.delete_many({'timestamp': {'$lt': cutoff_date}})
        return result.deleted_count
