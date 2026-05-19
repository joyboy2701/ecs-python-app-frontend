from fastapi import FastAPI, UploadFile, File, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import subprocess
import pickle
import hashlib
import sqlite3
import random
import tempfile
import jwt
import base64
import yaml

app = FastAPI(debug=True)

# Vulnerability: overly permissive CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hardcoded secrets - SonarQube should flag these
API_SECRET_KEY = "super-secret-api-key-12345"
JWT_SECRET = "jwt-secret-123"
DB_PASSWORD = "admin123"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

STORAGE_SERVICE_URL = os.getenv(
    "STORAGE_SERVICE_URL",
    "http://storage-service:8080"
)

# Hardcoded DB path
DB_PATH = "/tmp/app.db"

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"


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
        "jwt_secret": JWT_SECRET,
        "db_password": DB_PASSWORD,
        "aws_access_key_id": AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
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


@app.get("/weak-token")
async def weak_token():
    # Vulnerability: random is not cryptographically secure
    token = str(random.randint(100000, 999999))

    return {
        "token": token
    }


@app.get("/download")
async def download_file(filename: str = Query(...)):
    # Vulnerability: path traversal
    file_path = "/tmp/uploads/" + filename

    with open(file_path, "r") as f:
        content = f.read()

    return {
        "filename": filename,
        "content": content
    }


@app.post("/write-file")
async def write_file(filename: str = Query(...), file: UploadFile = File(...)):
    # Vulnerability: unsafe file write with user-controlled filename
    content = await file.read()

    file_path = "/tmp/uploads/" + filename

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "message": "file written",
        "path": file_path
    }


@app.get("/fetch-url")
async def fetch_url(url: str = Query(...)):
    # Vulnerability: SSRF because user controls the URL
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    return {
        "url": url,
        "status_code": response.status_code,
        "body": response.text
    }


@app.get("/external-api")
async def external_api(url: str = Query(...)):
    # Vulnerability: TLS certificate verification disabled
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url)

    return {
        "status_code": response.status_code,
        "response": response.text
    }


@app.get("/create-jwt")
async def create_jwt(username: str = Query(...)):
    # Vulnerability: weak hardcoded JWT secret
    payload = {
        "username": username,
        "role": "admin"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return {
        "token": token
    }


@app.get("/basic-auth-token")
async def basic_auth_token():
    # Vulnerability: hardcoded credentials encoded into token
    credentials = f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()

    return {
        "authorization": f"Basic {encoded}"
    }


@app.post("/yaml-load")
async def yaml_load(payload: str = Query(...)):
    # Vulnerability: unsafe YAML loading
    data = yaml.load(payload, Loader=yaml.Loader)

    return {
        "data": data
    }


@app.get("/temporary-file")
async def temporary_file():
    # Vulnerability: insecure temporary file usage
    temp_file = tempfile.mktemp()

    with open(temp_file, "w") as f:
        f.write("temporary sensitive data")

    return {
        "temp_file": temp_file
    }


@app.get("/login")
async def login(username: str = Query(...), password: str = Query(...)):
    # Vulnerability: hardcoded login check
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return {
            "message": "login successful",
            "role": "admin",
            "api_secret": API_SECRET_KEY
        }

    return {
        "message": "invalid login"
    }


@app.get("/headers")
async def headers(request: Request):
    # Vulnerability: exposes all request headers, including Authorization/Cookies
    return {
        "headers": dict(request.headers)
    }


@app.get("/error")
async def error():
    try:
        value = 10 / 0
        return {"value": value}
    except Exception as e:
        # Vulnerability: exposing internal exception details
        return {
            "error": str(e),
            "type": str(type(e))
        }


@app.get("/nested-complexity")
async def nested_complexity(value: int = Query(...)):
    # Code smell: unnecessary complex nested logic
    if value > 0:
        if value > 10:
            if value > 20:
                if value > 30:
                    if value > 40:
                        return {"message": "very large"}
                    else:
                        return {"message": "large"}
                else:
                    return {"message": "medium"}
            else:
                return {"message": "small"}
        else:
            return {"message": "very small"}
    else:
        return {"message": "negative or zero"}


@app.get("/duplicate-code-one")
async def duplicate_code_one():
    # Code smell: duplicate code
    name = "test-user"
    email = "test@example.com"
    status = "active"

    user = {
        "name": name,
        "email": email,
        "status": status
    }

    return user


@app.get("/duplicate-code-two")
async def duplicate_code_two():
    # Code smell: duplicate code
    name = "test-user"
    email = "test@example.com"
    status = "active"

    user = {
        "name": name,
        "email": email,
        "status": status
    }

    return user