from fastapi import FastAPI, UploadFile, File
import httpx
import os

app = FastAPI()

STORAGE_SERVICE_URL = os.getenv(
    "STORAGE_SERVICE_URL",
    "http://storage-service:8080"
)

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STORAGE_SERVICE_URL}/store",
            files={
                "file": (file.filename, await file.read(), file.content_type)
            }
        )
    return response.json()


# ✅ Health check endpoint
@app.get("/health")
async def health():
    # Optional: check if storage service is reachable
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get(f"{STORAGE_SERVICE_URL}/health")
            if r.status_code == 200:
                return {"status": "ok", "storage_service": "reachable"}
            else:
                return {"status": "ok", "storage_service": "unreachable"}
    except Exception:
        return {"status": "ok", "storage_service": "unreachable"}




