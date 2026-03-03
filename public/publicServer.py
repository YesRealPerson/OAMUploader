from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(
    title="OAM Uploader Public API"
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
    return FileResponse("/temp/testfile.txt")



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