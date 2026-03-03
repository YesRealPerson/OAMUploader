from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(
    title="OAM Uploader Private API"
)

# Methods
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