import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Redis URL from the environment variables
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
celery_app = Celery(
    "tasks",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks"]  # Point to the new tasks module
)

# Optional Celery configuration
celery_app.conf.update(
    task_track_started=True,
)

# Health check server for Cloud Run
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def start_health_server():
    port = int(os.getenv('HEALTH_PORT', 8081))
    server = HTTPServer(('', port), HealthHandler)
    server.serve_forever()

# Start health server in background thread
threading.Thread(target=start_health_server, daemon=True).start()