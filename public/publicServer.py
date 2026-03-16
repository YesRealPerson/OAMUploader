from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
import botocore.exceptions
from pathlib import Path
from pydantic import BaseModel, ConfigDict
import boto3
from dotenv import load_dotenv
import os
from typing import Dict, List
import httpx

s3_client = boto3.client("s3")

if(not os.getenv("PRODUCTION")):
    load_dotenv()

S3BUCKET = os.getenv("BUCKET_NAME")
cors_configuration = {
    'CORSRules': [
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]}

# Amazon s3 session
session = boto3.Session()
s3 = boto3.client('s3')
if(len(s3.list_buckets()["Buckets"]) == 0):
    print("Zero buckets!")
    if(os.getenv("AWS_ACCESS_KEY_ID") == "test"): # If we're in the testing environment we want to setup the bucket and cors policy 
        s3.create_bucket(Bucket=S3BUCKET)
        s3.put_bucket_cors(
            Bucket=S3BUCKET,
            CORSConfiguration=cors_configuration
        )
    else:
        raise ValueError("AWS S3 has zero buckets!")

buckets = [x['Name'] for x in s3.list_buckets()['Buckets']]

print("Buckets: ", buckets)
if(not S3BUCKET in buckets):
    raise ValueError(S3BUCKET+" does not exist on AWS S3!")

# FastAPI setup
app = FastAPI(
    title="OAM Uploader API Reference",
    description="""
[Home](/)
[Dashboard](/dashboard)
[Uploader](/upload)
"""
)

"""
Notes section:
TODO: DELETE ME LATER :)
TODO: Combine repeated body types when all finalized.
TODO: Add checking for the current user, currently the API is very insecure and will just let users interact with S3, NOT GOOD.
TODO: Remove raw responses later, currently only for debugging purposes
TODO: Remove list multipart uploads
TODO: Specify response schemas when everything is finalized
"""
CLIENT_ID = os.getenv("OAUTH_CLIENT")
CLIENT_SECRET = os.getenv("OAUTH_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
AUTHORIZE_URL_OSM = "https://www.openstreetmap.org/oauth2/authorize"
TOKEN_URL_OSM = "https://www.openstreetmap.org/oauth2/token"

# Example Methods
@app.get("/api/v1/login")
async def osmlogin():
    url = f"{AUTHORIZE_URL_OSM}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid"
    return RedirectResponse(url)

@app.get("/api/v1/authenticate")
async def authenticate(code: str):
    async with httpx.AsyncClient() as client:
        payload = {"grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI}
        response = await client.post(TOKEN_URL_OSM, data=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=400)
    token_data=response.json()
    return token_data

# Dashboard Endpoints
class GetEntriesBody(BaseModel):
    count: int
    user: str
@app.get("/api/v1/getEntries", tags=["Dashboard"])
async def GetEntries(body: GetEntriesBody):
    """
    Gets the next 'count' entries of the user.
    TODO: NOT IMPLEMENTED
    """
    return {
        "count": body.count,
        "user": body.user,
        "message": "Dummy response"
    }

class EditEntryBody(BaseModel):
    id: str
    user: str
    # TODO: Fillout with metadata form OIN specification
@app.patch("/api/v1/editEntry", tags=["Dashboard"])
async def EditEntry(body: EditEntryBody):
    """
    Edits a single entry
    TODO: NOT IMPLEMENTED
    """
    return {
        "user": body.user,
        "id": body.id,
        "message": "Dummy response"
    }

class DeleteEntryBody(BaseModel):
    id: str
    user: str
@app.delete("/api/v1/deleteentry", tags=["Dashboard"])
async def DeleteEntry(body: DeleteEntryBody):
    """
    Deletes the specified entry
    TODO: NOT IMPLEMENTED
    """
    return {
        "user": body.user,
        "id": body.id,
        "message": "Dummy response"
    }

# S3 Endpoints
@app.get("/api/v1/s3/listmultiparts", tags=["AWS S3"])
async def listmultipart():
    """
    Temporary endpoint to list s3 multipart uploads
    """
    try:
        return s3.list_multipart_uploads(Bucket=S3BUCKET)["Uploads"]
    except KeyError:
        raise HTTPException(status_code=400, detail="No uploads have been started!")
class createmultipartBody(BaseModel):
    filename: str
    metadata: Dict[str, str]
    contenttype: str
@app.post("/api/v1/s3/createmultipart", tags=["AWS S3"])
async def createmultipart(body: createmultipartBody):
    """
    Creates a multipart upload
    """
    userid = "c21782c1-873a-4b79-a3cf-c6a9d25c2e6a" # TODO: Replace me with actual UUID
    key = userid+"-"+body.filename
    response = s3.create_multipart_upload(
        Bucket=S3BUCKET,
        Metadata=body.metadata,
        Key=key,
        ContentType=body.contenttype
    )
    return {
        'key': key,
        'uploadId': response["UploadId"],
        'raw': response # For debugging purposes
    }

class abortmultipartBody(BaseModel):
    key: str
    uploadid: str
@app.post("/api/v1/s3/abortmultipart", tags=["AWS S3"])
async def abortmultipart(body: abortmultipartBody):
    try:
        s3.abort_multipart_upload(
            Bucket=S3BUCKET,
            Key=body.key,
            UploadId=body.uploadid
        )
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])
    return 200

class partSchema(BaseModel):
    ETag: str
    PartNumber: int
    model_config = ConfigDict(extra='allow')
class completemultipartBody(BaseModel):
    key: str
    uploadid: str
    parts: List[partSchema]
@app.post("/api/v1/s3/completemultipart", tags=["AWS S3"])
async def completemultipart(body: completemultipartBody):
    try:
        parts = [
            {
                "ETag": p.ETag,
                "PartNumber": p.PartNumber
            }
            for p in body.parts
        ]
        s3.complete_multipart_upload(
            Bucket=S3BUCKET,
            UploadId=body.uploadid,
            Key=body.key,
            MultipartUpload={
                "Parts": parts
            }
        )
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])
    return 200

class signedurlBody(BaseModel):
    key: str
    uploadid: str
    partnumber: int
@app.post("/api/v1/s3/signedurl", tags=["AWS S3"])
async def signedurl(body: signedurlBody):
    """
    Generates a presigned URL for multipart upload
    """
    if(not (0 < body.partnumber <= 10000)):
        raise HTTPException(status_code=400, detail="partnumber must be 1-10,000 (inclusive)!")
    params = {
        'Bucket': S3BUCKET,
        'Key': body.key,
        'PartNumber': body.partnumber,
        'UploadId': body.uploadid
    }
    try:
        url = s3.generate_presigned_url(ClientMethod="upload_part", Params=params, ExpiresIn=3600)
        return {
            'url': url
        }
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])

class listpartsBody(BaseModel):
    key: str
    uploadid: str
@app.post("/api/v1/s3/listparts", tags=["AWS S3"])
async def listparts(body: listpartsBody):
    """
    Returns the parts of a multipartupload that have already been uploaded
    """
    try:
        return s3.list_parts(Bucket=S3BUCKET, Key=body.key, UploadId=body.uploadid)["Parts"]
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])
    except KeyError as err: # The parts key will not exist if no parts have been uploaded
        raise HTTPException(status_code=400, detail="No parts uploaded!")

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
    elif ".css" in full_path or ".js" in full_path:
        full_path = "."+full_path
    else:
        full_path = "."+full_path+".html"
    file = STATIC / full_path
    print(full_path)
    if file.exists():
        return FileResponse(file)
    else:
        return FileResponse(STATIC / "404.html")