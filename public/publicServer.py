from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import httpx

import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client("s3")

app = FastAPI(
    title="OAM Uploader Public API"
)

CLIENT_ID = os.environ.get("OAUTH_CLIENT", "client")
CLIENT_SECRET = os.environ.get("OAUTH_SECRET", "secret")
REDIRECT_URI = "https://localhost:8080/api/v1/authenticate"
AUTHORIZE_URL = "https://www.openstreetmap.org/oauth2/authorize"
TOKEN_URL = "https://www.openstreetmap.org/oauth2/token"

# Example Methods
@app.get("/api/v1/login")
async def osmlogin():
    url = f"{AUTHORIZE_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid"
    return RedirectResponse(url)

@app.get("/api/v1/authenticate")
async def authenticate(code: str):
    async with httpx.AsyncClient() as client:
        payload = {"grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI}
        response = await client.post(TOKEN_URL, data=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=400)
    token_data=response.json()
    return token_data

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
        "message": f"Upload {id} has been successfully aborted."
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