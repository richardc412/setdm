from fastapi import FastAPI

app = FastAPI(title="SetDM API")


@app.get("/health")
def health():
    return {
        "ok": True,
    }
