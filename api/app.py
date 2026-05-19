# from fastapi import FastAPI, UploadFile, File
# import httpx
# import os

# app = FastAPI()

# STORAGE_SERVICE_URL = os.getenv(
#     "STORAGE_SERVICE_URL",
#     "http://storage-service:8080"
# )

# @app.post("/upload")
# async def upload(file: UploadFile = File(...)):
#     async with httpx.AsyncClient() as client:
#         response = await client.post(
#             f"{STORAGE_SERVICE_URL}/store",
#             files={
#                 "file": (file.filename, await file.read(), file.content_type)
#             }
#         )
#     return response.json()

# @app.get("/files")
# async def list_files():
#     """Fetch all files from the storage service"""
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{STORAGE_SERVICE_URL}/files")
#     return response.json()

# # ✅ Health check endpoint
# @app.get("/health")
# async def health():
#     # Optional: check if storage service is reachable
#     try:
#         async with httpx.AsyncClient(timeout=2) as client:
#             r = await client.get(f"{STORAGE_SERVICE_URL}/health")
#             if r.status_code == 200:
#                 return {"status": "ok", "storage_service": "reachable"}
#             else:
#                 return {"status": "ok", "storage_service": "unreachable"}
#     except Exception:
#         return {"status": "ok", "storage_service": "unreachable"}
 
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
        # Bad practice: swallowing all exceptions silently
        return {"status": "ok", "storage_service": "unreachable"}


@app.get("/debug")
async def debug():
    # Information disclosure - exposes sensitive/internal config
    return {
        "storage_service_url": STORAGE_SERVICE_URL,
        "api_secret_key": API_SECRET_KEY,
        "db_path": DB_PATH
    }


@app.get("/run-command")
async def run_command(cmd: str = Query(...)):
    # Command injection vulnerability
    output = subprocess.check_output(cmd, shell=True)

    return {
        "command": cmd,
        "output": output.decode("utf-8", errors="ignore")
    }


@app.get("/user")
async def get_user(username: str = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # SQL injection vulnerability
    query = f"SELECT id, username, email FROM users WHERE username = '{username}'"

    cursor.execute(query)
    result = cursor.fetchall()

    conn.close()

    return {
        "query": query,
        "result": result
    }


@app.post("/deserialize")
async def deserialize(payload: bytes = File(...)):
    # Insecure deserialization vulnerability
    obj = pickle.loads(payload)

    return {
        "message": "Object deserialized",
        "object": str(obj)
    }


@app.get("/divide")
async def divide(a: int, b: int):
    # Bug: possible division by zero
    result = a / b

    return {
        "result": result
    }


@app.get("/unused")
async def unused_code():
    unused_variable = "this variable is never used"

    x = 10
    y = 20

    # Code smell: redundant condition
    if x < y:
        return {"message": "x is smaller"}
    else:
        return {"message": "x is not smaller"}
