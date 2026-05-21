from fastapi import FastAPI
import random, string

app = FastAPI()

@app.post("/shorten")
def shorten_url (url: str):
    if url.startswith("http://") or url.startswith("https://"):
        return {"url": url}
    else:
        return {"error": "Invalid URL"}
