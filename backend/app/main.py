from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.auth import auth_router

app = FastAPI(title="SetDM API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router)


@app.get("/health")
def health():
    return {
        "ok": True,
    }
