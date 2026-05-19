
 
from fastapi import FastAPI, UploadFile, File, Query
import httpx
import os
import subprocess
import pickle
import hashlib
import sqlite3

app = FastAPI()

# Hardcoded secret - SonarQube should flag this
API_SECRET_KEY = "super-secret-api-key-12345"

STORAGE_SERVICE_URL = os.getenv(
    "STORAGE_SERVICE_URL",
    "http://storage-service:8080"
)

# Hardcoded DB path
DB_PATH = "/tmp/app.db"


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Bug: reading full file into memory without size validation
    file_content = await file.read()

    # Weak hash algorithm - SonarQube should flag MD5 usage
    file_hash = hashlib.md5(file_content).hexdigest()

    # Bug: no validation of filename or content type
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STORAGE_SERVICE_URL}/store",
            files={
                "file": (file.filename, file_content, file.content_type)
            }
        )

    # Bug: blindly trusting downstream service response
    result = response.json()
    result["file_hash"] = file_hash

    return result


@app.get("/files")
async def list_files():
    """Fetch all files from the storage service"""

    # Bug: no timeout configured
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE_URL}/files")

    return response.json()


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get(f"{STORAGE_SERVICE_URL}/health")
            if r.status_code == 200:
                return {"status": "ok", "storage_service": "reachable"}
            else:
                return {"status": "ok", "storage_service": "unreachable"}
    except Exception:
        return {"status": "ok", "storage_service": "unreachable"}
#SECRET_KEY = AII23SANFJWSF    
