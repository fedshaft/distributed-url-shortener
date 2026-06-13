import time
from locust import HttpUser, task, between

class QuickstartUser(HttpUser):
    wait_time = between(1,2)
    @task
    def on_start(self):
        self.client.allow_redirects = False
