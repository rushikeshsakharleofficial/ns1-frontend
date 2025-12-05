import os
import time
import subprocess
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import config

# Setup logging
logging.basicConfig(
    filename='/var/log/dns-watcher.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

class ZoneFileHandler(FileSystemEventHandler):
    """
    Watches for changes in the DNS zone directory.
    When a zone file (.hosts or .rev) is modified, it triggers a sync to NS2.
    """
    
    def __init__(self):
        self.last_sync = {}
        self.debounce_seconds = 5

    def on_modified(self, event):
        if event.is_directory:
            return
            
        filename = os.path.basename(event.src_path)
        
        # Only interest in our zone files
        if filename.endswith(config.FORWARD_ZONE_PATTERN) or filename.endswith(config.REVERSE_ZONE_PATTERN):
            
            # Debounce: Prevent double firing for the same file in short succession
            current_time = time.time()
            if filename in self.last_sync:
                if (current_time - self.last_sync[filename]) < self.debounce_seconds:
                    return
            
            self.last_sync[filename] = current_time
            logging.info(f"File modified: {filename}. Triggering slave sync...")
            self.sync_slaves(filename)

    def sync_slaves(self, filename):
        """Sends HTTP sync triggers to all slaves"""
        import requests
        
        if not config.SLAVE_SERVERS:
            logging.warning("No SLAVE_SERVERS configured. Skipping sync.")
            return

        port = config.SLAVE_API_PORT
        secret = config.SLAVE_SECRET
        
        payload = {
            'filename': filename,
            'secret': secret
        }
        
        for host in config.SLAVE_SERVERS:
            url = f"http://{host}:{port}/sync"
            
            try:
                logging.info(f"Syncing to {host} via API...")
                
                resp = requests.post(url, json=payload, timeout=5)
                
                if resp.status_code == 200:
                    logging.info(f"SUCCESS: Synced {filename} to {host}.")
                else:
                    logging.error(f"FAILURE: {host} returned {resp.status_code}: {resp.text}")
                    
            except Exception as e:
                logging.error(f"EXCEPTION syncing to {host}: {str(e)}")

def start_watcher():
    path = config.NAMED_ZONE_DIR
    
    if not os.path.exists(path):
        logging.error(f"Zone directory {path} does not exist!")
        return

    logging.info(f"Starting DNS Watcher on: {path}")
    logging.info(f"Configured Slaves: {config.SLAVE_SERVERS}")
    logging.info(f"Slave API Port: {config.SLAVE_API_PORT}")

    event_handler = ZoneFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()


if __name__ == "__main__":
    start_watcher()
