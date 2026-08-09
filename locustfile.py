from locust import task
from locust.contrib.fasthttp import FastHttpUser

TEST_URL = "https://example.com/loadtest"

class CachedRedirectUser(FastHttpUser):
    def on_start(self):
        resp = self.client.post("/shorten", json={"url": TEST_URL}, name="/shorten")
        self.short_code = resp.json()["short_code"]
    @task
    def cached_redirect(self):
        with self.client.get(
            f"/{self.short_code}", name="/{short_code}", allow_redirects=False, catch_response=True
        ) as resp:
            if resp.status_code == 302:
                resp.success()
            else:
                resp.failure(f"expected 302, got {resp.status_code}")
