from flask import Flask, request, jsonify
import os
import subprocess
import logging
from config import config

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    filename='/var/log/dns-slave-agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

@app.route('/sync', methods=['POST'])
def sync_zone():
    """
    Receives a sync request from Master.
    Payload: {"filename": "example.com.hosts", "secret": "..."}
    """
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Verify Secret (Simple security)
    if data.get('secret') != config.SLAVE_SECRET:
        logging.warning(f"Invalid secret attempt from {request.remote_addr}")
        return jsonify({'error': 'Unauthorized'}), 401
        
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename missing'}), 400
        
    # Security: Ensure filename is just a basename, no paths
    filename = os.path.basename(filename)
    
    slave_dir = config.SLAVE_DIR
    file_path = os.path.join(slave_dir, filename)
    
    try:
        logging.info(f"Received sync request for {filename}")
        
        # 1. Remove the slave file to force re-transfer
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Deleted file: {file_path}")
        else:
            logging.info(f"File not found (already deleted?): {file_path}")
            
        # 2. Restart Named
        cmd = [config.SYSTEMCTL_PATH, 'restart', 'named']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Named service restarted successfully")
            return jsonify({'success': True, 'message': 'Sync complete'}), 200
        else:
            logging.error(f"Failed to restart named: {result.stderr}")
            return jsonify({'success': False, 'error': result.stderr}), 500
            
    except Exception as e:
        logging.error(f"Exception during sync: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('SLAVE_API_PORT', 5000))
    app.run(host='0.0.0.0', port=port)
