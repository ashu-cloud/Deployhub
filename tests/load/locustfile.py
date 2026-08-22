import hmac
import hashlib
import json
import uuid
from locust import HttpUser, task, between

class WebhookStormUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        # Setup specific to a user
        self.project_id = str(uuid.uuid4())
        self.secret = b"test_secret"
        
    @task
    def simulate_webhook_push(self):
        payload = {
            "ref": "refs/heads/main",
            "after": str(uuid.uuid4().hex),
            "repository": {
                "clone_url": "https://github.com/test/repo"
            }
        }
        payload_bytes = json.dumps(payload).encode('utf-8')
        
        # Calculate HMAC
        mac = hmac.new(self.secret, msg=payload_bytes, digestmod=hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"
        
        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
            "X-GitHub-Delivery": str(uuid.uuid4()),
            "X-GitHub-Event": "push"
        }
        
        # We assume the project service is running locally on port 8000
        # In actual testing, they'd run via docker-compose on the same network
        self.client.post(f"/webhooks/github/{self.project_id}", data=payload_bytes, headers=headers)
