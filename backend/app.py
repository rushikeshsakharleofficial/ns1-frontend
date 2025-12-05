from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
from config import config

# Create Flask application
app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = config.SECRET_KEY

# Enable CORS for API routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Import route blueprints
from routes.auth_routes import auth_bp
from routes.zone_routes import zone_bp
from routes.record_routes import record_bp
from routes.service_routes import service_bp
from routes.log_routes import log_bp
from routes.validation_routes import validation_bp
from routes.user_routes import user_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(zone_bp, url_prefix='/api')
app.register_blueprint(record_bp, url_prefix='/api')
app.register_blueprint(service_bp, url_prefix='/api')
app.register_blueprint(log_bp, url_prefix='/api')
app.register_blueprint(validation_bp, url_prefix='/api')
app.register_blueprint(user_bp, url_prefix='/api')


# Serve frontend
@app.route('/')
def index():
    """Serve the main frontend page"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('../frontend', path)


# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'service': 'DNS Manager API',
        'version': '1.0.0',
        'status': 'running'
    }), 200


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print(f"🚀 DNS Manager API starting on port {config.FLASK_PORT}...")
    print(f"📡 Frontend available at: http://localhost:{config.FLASK_PORT}")
    print(f"🔧 API base URL: http://localhost:{config.FLASK_PORT}/api")
    
    app.run(
        host='0.0.0.0',
        port=config.FLASK_PORT,
        debug=(config.FLASK_ENV == 'development')
    )
