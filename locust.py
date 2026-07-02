import time
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(1,2)
    @task
    def shorten_url(self):
        self.client.post("/shorten", json={"url": "https://www.goog.e"})
    
    @task
    def redirect(self):
        self.client.get("/abc123")
