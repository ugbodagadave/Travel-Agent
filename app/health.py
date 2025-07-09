# health.py
import os
import threading
import time
from flask import Flask

# Create Flask app for health checks
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/')
def root():
    return {'status': 'Celery worker running'}, 200

def run_health_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    # Start health server in background thread
    health_thread = threading.Thread(target=run_health_server)
    health_thread.daemon = True
    health_thread.start()
    
    # Give health server time to start
    time.sleep(3)
    print("Health server started on port", os.environ.get('PORT', 8080))
    
    # Import and start Celery worker
    try:
        from app.celery_worker import celery_app
        print("Starting Celery worker...")
        celery_app.worker_main(['worker', '--loglevel=info'])
    except ImportError as e:
        print(f"Error importing Celery app: {e}")
        # Keep the health server running
        while True:
            time.sleep(60)