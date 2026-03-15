from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import botocore.exceptions
from pathlib import Path
from pydantic import BaseModel
import boto3
from dotenv import load_dotenv
import os
from typing import Dict

load_dotenv()

# Amazon s3 session
session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_PUBLIC_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")
)
s3 = boto3.client('s3')
if(len(s3.list_buckets()["Buckets"]) == 0):
    print("Zero buckets!")
    if(os.getenv("AWS_SECRET_KEY") == "test"):
        s3.create_bucket(Bucket=os.getenv("BUCKET_NAME"))
    else:
        raise ValueError("AWS S3 has zero buckets!")

buckets = [x['Name'] for x in s3.list_buckets()['Buckets']]

print("Buckets: ", buckets)
if(not os.getenv("BUCKET_NAME") in buckets):
    raise ValueError(os.getenv("BUCKET_NAME")+" does not exist on AWS S3!")

app = FastAPI(
    title="OAM Uploader Public API"
)

"""
Notes section:
TODO: DELETE ME LATER :)
TODO: Combine repeated body types when all finalized.
"""

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

"""
S3 endpoints
TODO: Add checking for the current user
the current user should not have more than 1 (?) upload at a time to prevent abuse, push id to list on create, pop on abort or complete
TODO: Remove raw responses later, currently only for debugging purposes
TODO: Remove list multipart uploads
TODO: Add field validation for createmultipart
"""
@app.get("/api/v1/s3/listmultiparts", tags=["AWS S3"])
async def listmultipart():
    """
    Temporary endpoint to list s3 multipart uploads
    """
    response = s3.list_multipart_uploads(Bucket=os.getenv("BUCKET_NAME"))
    if("Uploads" not in response.keys()):
        return []
    return response["Uploads"]
class createmultipartBody(BaseModel):
    filename: str
    metadata: Dict[str, str]
@app.post("/api/v1/s3/createmultipart", tags=["AWS S3"])
async def createmultipart(body: createmultipartBody):
    """
    Creates a multipart upload
    """
    userid = "c21782c1-873a-4b79-a3cf-c6a9d25c2e6a" # TEMP, REPLACE ME LATER
    key = userid+"-"+body.filename
    response = s3.create_multipart_upload(
        Bucket=os.getenv("BUCKET_NAME"),
        Metadata=body.metadata,
        Key=key
    )
    return {
        'key': key,
        'id': response["UploadId"],
        'raw': response
    }

class abortmultipartBody(BaseModel):
    key: str
    uploadid: str
@app.post("/api/v1/s3/abortmultipart", tags=["AWS S3"])
async def abortmultipart(body: abortmultipartBody):
    try:
        s3.abort_multipart_upload(
            Bucket=os.getenv("BUCKET_NAME"),
            Key=body.key,
            UploadId=body.uploadid
        )
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])
    return 200

class completemultipartBody(BaseModel):
    key: str
@app.post("/api/v1/s3/completemultipart", tags=["AWS S3"])
async def completemultipart(body: completemultipartBody):
    try:
        s3.complete_multipart_upload(
            Bucket=os.getenv("BUCKET_NAME"),
            Key=body.key
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
        'Bucket': os.getenv("BUCKET_NAME"),
        'Key': body.key,
        'PartNumber': body.partnumber,
        'UploadId': body.uploadid
    }
    try:
        url = s3.generate_presigned_url(ClientMethod="upload_part", Params=params)
        return url
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])

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