from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# Methods
@app.get("/api/v1/test")
async def TestMethod():
    return {"message": "What's up?"}

# Serve frontend
STATIC = Path(__file__).parent / "static"
@app.get("{full_path:path}")
async def ServeHTML(full_path: str):
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