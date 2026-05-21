from fastapi import FastAPI
import random, string

app = FastAPI()

storage = {}

@app.post("/shorten")
async def shorten_url (url: str):
    if url.startswith("http://") or url.startswith("https://"):
        if url not in storage:
            storage[url] = ''.join(random.choices(string.ascii_letters + string.digits, k = 6))
            return {"shortened_url": storage[url]}
        else:
            return {"shortened_url": storage[url]}
    else:
        return {"error": "Invalid URL"}

