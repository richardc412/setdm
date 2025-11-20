from fastapi import FastAPI

app = FastAPI(title="Hackathon API")

@app.get("/health")
def health():
    return {"ok": True}
