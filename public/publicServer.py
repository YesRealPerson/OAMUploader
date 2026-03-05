from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(
    title="OAM Uploader Public API"
)

# Example Methods
@app.get("/api/v1/test")
async def TestMethod():
    """
    Hello world!
    """
    return {"message": "What's up?"}

@app.get("/api/v1/readShared")
async def TestMethod():
    """
    Reads a shared file from the /temp directory!
    """
    return FileResponse("/temporary/testfile.txt")

@app.get("/api/v1/writeShared")
async def TestMethod():
    """
    Appends an 'a' to the shared file
    """
    with open("/temporary/testfile.txt", "a", encoding="utf-8") as f:
        f.write("a")
    return FileResponse("/temporary/testfile.txt")



@app.delete("/api/v1/uploads/{id}")
async def cancel_upload(id: str):
    # TODO: Verify user owns this upload via OAuth token
    # TODO: Abort S3 multipart upload
    # TODO: Update database status to canceled
    
    return {
        "status": "success",
        "message": f"Upload {id} has been successfully aborted.",
        "dummy_data": True
    }

# Serve HTML, keep at bottom
STATIC = Path(__file__).parent / "static"
@app.get("{full_path:path}")
async def ServeHTML(full_path: str):
    """
    Serves static web files (HTML, CSS, etc.)
    """
    if full_path == "/" or full_path == "":
        full_path = "index.html"
    else:
        full_path = "."+full_path+".html"
    file = STATIC / full_path
    print(full_path)
    if file.exists():
        return FileResponse(file)
    else:
        return FileResponse(STATIC / "404.html")