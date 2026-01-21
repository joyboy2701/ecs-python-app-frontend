from fastapi import FastAPI, UploadFile, File
import os
from uuid import uuid4
from fastapi.responses import JSONResponse
import datetime

app = FastAPI()

STORAGE_PATH = "/data"
os.makedirs(STORAGE_PATH, exist_ok=True)

# Health check endpoint 
# Health check endpoint 
@app.get("/health")
async def health_check():
    """Health check endpoint for ECS/liveness probes"""
    try:
        # Check if storage directory is writable
        test_file = os.path.join(STORAGE_PATH, f".healthcheck-{uuid4()}")
        with open(test_file, 'w') as f:
            f.write("healthcheck")
        os.remove(test_file)
        
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "storage-service",
                "timestamp": datetime.datetime.now().isoformat(),
                "storage_path": STORAGE_PATH,
                "storage_writable": True
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "unhealthy",
                "service": "storage-service",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint to verify service is running"""
    return {
        "message": "Storage Service API",
        "endpoints": {
            "GET /": "This info",
            "GET /health": "Health check",
            "POST /store": "Upload file",
            "GET /files": "List stored files (optional)"
        },
        "timestamp": datetime.datetime.now().isoformat()
    }

# Optional: Add endpoint to list stored files
@app.get("/files")
async def list_files():
    """List all stored files"""
    try:
        files = os.listdir(STORAGE_PATH)
        return {
            "files": files,
            "count": len(files),
            "path": STORAGE_PATH
        }
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/store")
async def store_file(file: UploadFile = File(...)):
    """Store uploaded file"""
    filename = f"{uuid4()}-{file.filename}"
    filepath = os.path.join(STORAGE_PATH, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    return {
        "message": "File stored successfully",
        "path": filename,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": os.path.getsize(filepath),
        "timestamp": datetime.datetime.now().isoformat()
    }

# Optional: Add endpoint to get file info
@app.get("/files/{filename}")
async def get_file_info(filename: str):
    """Get information about a specific file"""
    filepath = os.path.join(STORAGE_PATH, filename)
    
    if not os.path.exists(filepath):
        return JSONResponse(
            content={"error": "File not found"},
            status_code=404
        )
    
    return {
        "filename": filename,
        "path": filepath,
        "size": os.path.getsize(filepath),
        "created": datetime.datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
        "modified": datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
    }





