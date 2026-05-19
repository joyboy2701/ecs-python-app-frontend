from fastapi import FastAPI, UploadFile, File, Query
import httpx
import os
import hashlib
import sqlite3
import random
import requests

app = FastAPI()

# Hardcoded credentials/security-sensitive values
# These variable names are more likely to trigger SonarQube hardcoded credential rules.
PASSWORD = "Admin@123456"
DB_PASSWORD = "mysql-root-password"
DATABASE_PASSWORD = "prod-db-password"
AWS_SECRET_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
JWT_SECRET = "my-super-secret-jwt-key"
API_TOKEN = "hardcoded-api-token-123456"

STORAGE_SERVICE_URL = os.getenv(
    "STORAGE_SERVICE_URL",
    "http://storage-service:8080"
)

DB_PATH = "/tmp/app.db"


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_content = await file.read()

    # Security Hotspot: weak hashing algorithm
    file_hash = hashlib.md5(file_content).hexdigest()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{STORAGE_SERVICE_URL}/store",
            files={
                "file": (file.filename, file_content, file.content_type)
            }
        )

    result = response.json()
    result["file_hash"] = file_hash

    return result


@app.get("/files")
async def list_files():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE_URL}/files")

    return response.json()


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get(f"{STORAGE_SERVICE_URL}/health")

            # Code smell: identical branches
            if r.status_code == 200:
                return {"status": "ok"}
            else:
                return {"status": "ok"}

    except Exception:
        # Code smell: broad exception handling
        return {"status": "ok"}


@app.get("/debug")
async def debug():
    # Vulnerability / Hotspot: exposing hardcoded secrets in API response
    return {
        "password": PASSWORD,
        "db_password": DB_PASSWORD,
        "database_password": DATABASE_PASSWORD,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
        "jwt_secret": JWT_SECRET,
        "api_token": API_TOKEN,
        "storage_service_url": STORAGE_SERVICE_URL,
        "db_path": DB_PATH,
    }


@app.get("/weak-random-token")
async def weak_random_token():
    # Security Hotspot: random is not secure for security-sensitive tokens
    token = random.randint(100000, 999999)

    return {
        "token": token
    }


@app.get("/unsafe-eval")
async def unsafe_eval(expression: str = Query(...)):
    # Vulnerability / Security Hotspot: dynamic code execution
    result = eval(expression)

    return {
        "expression": expression,
        "result": result
    }


@app.get("/insecure-request")
async def insecure_request():
    # Security Hotspot: SSL certificate verification disabled
    response = requests.get(
        "https://example.com",
        verify=False
    )

    return {
        "status_code": response.status_code
    }


@app.get("/user")
async def get_user(username: str = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vulnerability candidate: SQL query built using user input
    query = "SELECT id, username, email FROM users WHERE username = '" + username + "'"

    cursor.execute(query)
    result = cursor.fetchall()

    conn.close()

    return {
        "query": query,
        "result": result
    }


@app.get("/divide-by-zero")
async def divide_by_zero():
    # Bug: obvious division by zero
    result = 10 / 0

    return {
        "result": result
    }


@app.get("/same-expression")
async def same_expression(value: int):
    # Bug / Code smell: same expression on both sides
    if value == value:
        return {"message": "same"}
    else:
        return {"message": "not same"}


@app.get("/duplicate-branches")
async def duplicate_branches(is_admin: bool):
    # Code smell: both branches return the same thing
    if is_admin:
        return {"access": "allowed"}
    else:
        return {"access": "allowed"}


@app.get("/unused-variable")
async def unused_variable():
    # Code smell candidate: unused local variable
    unused_password = "this-password-is-not-used"

    return {
        "message": "This endpoint has an unused variable"
    }


@app.get("/too-complex")
async def too_complex(role: str, active: bool, verified: bool, paid: bool):
    # Code smell candidate: unnecessarily complex conditional logic
    if role == "admin":
        if active:
            if verified:
                if paid:
                    return {"access": "full"}
                else:
                    return {"access": "limited"}
            else:
                return {"access": "denied"}
        else:
            return {"access": "denied"}
    elif role == "user":
        if active:
            if verified:
                return {"access": "basic"}
            else:
                return {"access": "denied"}
        else:
            return {"access": "denied"}
    else:
        return {"access": "denied"}