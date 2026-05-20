from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI, HTTPException, Depends, Cookie, Request
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
import botocore.exceptions
from pathlib import Path
from pydantic import BaseModel, ConfigDict
import boto3
import httpx
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
from typing import Dict, List
from jose import ExpiredSignatureError, JWTError, jwt
from kubernetes import client, config
# from hotosm_auth import AuthConfig
# from hotosm_auth_fastapi import init_auth, osm_router, CurrentUser
import uuid
import re

# Environment configuration

if(not os.getenv("PRODUCTION")):
    load_dotenv()
CLIENT_ID = os.environ.get("OSM_CLIENT_ID", "test")
CLIENT_SECRET = os.environ.get("OSM_CLIENT_SECRET", "test")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "test")
AUTHORIZE_URL = os.environ.get("AUTHORIZE_URL", "test")
TOKEN_URL = os.environ.get("TOKEN_URL", "test")
STAC_URL = os.environ.get("STAC_URL", "http://stac-api:8082")
WF_FRONT_URL = os.environ.get("WF_FRONT_URL", "http://front-api.default.svc.cluster.local:12345")
WF_AWS_URL = os.environ.get("WF_AWS_URL", "http://local:4566")
WF_STAC_URL = os.environ.get("WF_STAC_URL", "http://stac-api.default.svc.cluster.local:8082")
# TODO: Depreciate old authentication system
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 1
REFRESH_TOKEN_DAYS = 30

"""
Kubernetes API setup
"""
try:
    config.load_incluster_config() # In cluster testing/production
except config.ConfigException:
    config.load_kube_config() # FastAPI testing
k8s_api = client.CustomObjectsApi()


"""
Amazon s3 session
"""
session = boto3.Session()
s3 = boto3.client('s3', region_name=os.environ.get("AWS_REGION", "us-east-1"))
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

"""
FastAPI Setup
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: Setup HOTOSM auth
    # auth_config = AuthConfig.from_env()
    # init_auth(auth_config)
    yield
# app.include_router(osm_router, prefix="/api/auth/osm")

app = FastAPI(
    title="OAM Uploader API Reference",
    description="""
[Home](/)
[Dashboard](/dashboard)
[Uploader](/upload)""", # Links back to homepage on API docs page
lifespan=lifespan
)


"""
Voltile data structures for storing server states

NOTE: Some of these will be migrated to a formal database later. AWS KV store seems like an easy integration.
"""
# Potentially useless schemas for later
class User(BaseModel):
    username: str
    user_id: str
    expires_at: datetime
    created_at: datetime
class Upload(BaseModel):
    id: str
    status: str
    state: str
    message: str
    userid: str
    filename: str

userdb:dict[str, User] = {} # Poor mans database for user refresh tokens
uploaddb:dict[str, Upload] = {} # Poor mans database for in progress uploads
usertoupload:dict[str,set[str]] = {} # User IDs > Upload IDs
validStates = set() # Set of valid ongoing uploads


"""
Authentication helper functions

NOTE: These will be depreciated upon successful implementation of HOTOSM Auth
"""
def create_session_token(user_id: str, username: str):
    """
    Creates a JWT session token
    """
    now = datetime.now(timezone.utc) 

    payload = {
        "sub": str(user_id),
        "username": str(username),
        "exp": int((now + timedelta(hours=JWT_EXPIRE_HOURS)).timestamp()),
        "iat": int(now.timestamp()),
        "iss": "OAMUploader",
        "type": "access"
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    if str(user_id) not in usertoupload:
        usertoupload[str(user_id)] = set()
    return token
def create_refresh_token():
    return secrets.token_urlsafe(64)
def get_current_user_helper(session):
    payload = jwt.decode(session, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    usertoupload[payload['sub']] # Triggers keyerror if user not in database
    return payload
def get_current_user(session: str = Cookie(None)):
    if not session:
        raise HTTPException(status_code=401, detail="Not logged in")
    try:
        return get_current_user_helper(session)
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid session")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Expired session")
    except KeyError:
        raise HTTPException(status_code=401, detail="Not logged in")

"""
Random Helpers
"""
def slugify(text):
    # 1. Replace spaces with nothing (per your original logic) or hyphens
    # 2. Remove anything that isn't a word character (a-z, 0-9) or a hyphen/underscore
    # 3. Optional: Lowercase it for consistency
    # generated by GPT
    safe_text = re.sub(r'[^a-zA-Z0-9_\-]', '', text.replace(" ", ""))
    return safe_text

"""
Internal interaction functions

TODO: Add endpoint for user to kill processing
"""
def invoke_processing(s3_path: str, filename:str, key:str, userid: str):
    """
    Schedules an Argo Workflows event to process an uploaded TIF file
    """
    uploadid = str(uuid.uuid4())
    state = str(uuid.uuid4())
    manifest = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Workflow",
        "metadata": {
            "generateName": "geotiff-run-"
        },
        "spec": {
            "workflowTemplateRef": {
                "name": "geotiff-processing-template"
            },
            "arguments": {
                "parameters": [
                    {"name": "s3-path", "value": s3_path},
                    {"name": "filename", "value": filename},
                    {"name": "bucket", "value": S3BUCKET},
                    {"name": "key", "value": key},
                    {"name": "id", "value": uploadid},
                    {"name": "uuid", "value": userid},
                    {"name": "state", "value": state},
                    {"name": "externalaws", "value": os.getenv("EXTERNAL_S3_ENDPOINT", "http://localhost:4566")},
                    {"name": "stacurl", "value": WF_STAC_URL},
                    {"name": "awsurl", "value": WF_AWS_URL},
                    {"name": "fronturl", "value": WF_FRONT_URL},
                ]
            }
        }
    }
    validStates.add(state)
    uploaddb[uploadid] = Upload(id=uploadid, status="Processing", message="Waiting for updates.", state=state, userid=userid, filename=filename)
    usertoupload[userid].add(uploadid)
    return k8s_api.create_namespaced_custom_object(
        group="argoproj.io",
        version="v1alpha1",
        namespace="argo",
        plural="workflows",
        body=manifest,
    )

class WorkflowStatusUpdate(BaseModel):
    id: str
    status: str
    message: str=""
@app.post("/api/v1/workflowstatus", include_in_schema=False)
async def callback(body: WorkflowStatusUpdate, request: Request):
    """
    Workflows attempts to call this endpoint to update the state of a given upload
    Requires that the workflow pass a valid state

    TODO: If the workflow passes an invalid state kill the workflow
    """
    token = request.headers.get("X-Internal-Token")
    if(token not in validStates or body.id not in uploaddb.keys()):
        raise HTTPException(401)
    uploaddb[body.id].status = body.status
    uploaddb[body.id].message = body.message
    if(body.status == "Succeeded" or body.status == "Failed" or body.status == "Error"):
        validStates.remove(token)
        if not body.status == "Failed":
            usertoupload[uploaddb[body.id].userid].remove(body.id)
    return {"ok": True}

@app.delete("/api/v1/deleteupload", tags=["Dashboard"])
async def DeleteUpload(id: str, user=Depends(get_current_user)):
    """
    Deletes a failed upload from the user's upload list.
    """
    if id not in uploaddb:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload = uploaddb[id]

    if upload.userid != user["sub"]:
        raise HTTPException(status_code=401)

    if upload.status not in {"Failed", "Error"}:
        raise HTTPException(
            status_code=400,
            detail="Only failed uploads can be deleted from the upload list"
        )
    print(upload.status)
    # validStates.discard(upload.state)
    # usertoupload.get(user["sub"], set()).discard(id)
    # del uploaddb[id]

    return {"ok": True}


"""
Authentication endpoints

NOTE: These will be depreciated upon successful implementation of HOTOSM Auth
"""
@app.get("/api/v1/login", tags=["redirects"])
async def osmlogin():
    """Generate OSM login URL"""
    state = secrets.token_urlsafe(32)
    url = f"{AUTHORIZE_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&state={state}&scope=openid read_prefs"
    response = RedirectResponse(url)
    response.set_cookie("oauth_state", state, httponly=True, samesite="lax")
    return response
@app.post("/api/v1/refresh", tags=["authentication"])
async def refreshsession(refresh: str = Cookie(None)):
    """
    Attempt to refresh session token
    
    NOTE: Broken lmao
    """
    if not refresh:
        raise HTTPException(status_code=401)
    try:
        user:User = userdb[refresh]
    except KeyError:
        raise HTTPException(status_code=401)
    now = datetime.now(timezone.utc)
    if now > user.expires_at:
        raise HTTPException(status_code=401)
    
    response = JSONResponse({"ok": True})
    response.set_cookie(
        key="session",
        value=create_session_token(user.user_id, user.username),
        httponly=True,
        secure=os.getenv("AWS_ACCESS_KEY_ID") != "test",
        samesite="lax",
        max_age=60 * 60
    )
    new_refresh = create_refresh_token()
    del userdb[refresh]   # invalidate old token
    userdb[new_refresh] = user

    response.set_cookie(
        key="refresh",
        value=new_refresh,
        httponly=True,
        secure=os.getenv("AWS_ACCESS_KEY_ID") != "test",
        samesite="strict",
        max_age=60 * 60 * 24 * 30
    )

    return response

@app.get("/api/v1/authorize", tags=["authentication"])
async def authenticate(code: str, state: str, oauth_state: str = Cookie(None)):
    """
    Attempt to authenticate with OSM and store user information if successful.
    """
    if state != oauth_state:
        raise HTTPException(status_code=400, detail="OAuth state mismatch")
    # Get tokens
    async with httpx.AsyncClient() as client:
        payload = {"grant_type": "authorization_code",
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI}
        response = await client.post(TOKEN_URL, data=payload)
    if response.status_code != 200:
        if(500 > response.status_code >= 400):
            print("we potentially fucked up:",response.read())
        raise HTTPException(status_code=response.status_code)
    token_data=response.json()

    # Get user info
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": "Bearer "+token_data["access_token"]
        }
        response = await client.get("https://api.openstreetmap.org/api/0.6/user/details.json", headers=headers)

    if response.status_code != 200:
        if(500 > response.status_code >= 400):
            print("we potentially fucked up:",response.read())
        raise HTTPException(status_code=response.status_code)
    
    # get user_data
    user_data=response.json()["user"]
    # Generate JWT and register to database
    jwtToken = create_session_token(user_data["id"],user_data["display_name"])
    response = RedirectResponse("/dashboard")

    response.set_cookie(
        key="session",
        value=jwtToken,
        httponly=True,
        secure= os.getenv("AWS_ACCESS_KEY_ID") != "test", # IF we're testing, don't require https
        samesite="lax",
        max_age=60 * 60
    )

    refreshToken = create_refresh_token()
    response.set_cookie(
        key="refresh",
        value=refreshToken,
        httponly=True,
        secure= os.getenv("AWS_ACCESS_KEY_ID") != "test", # IF we're testing, don't require https
        samesite="strict",
        max_age=60 * 60 * 24 * 30
    )
    now = datetime.now(timezone.utc)
    userdb[refreshToken] = User(username=user_data["display_name"], user_id=(str)(user_data["id"]), expires_at=now + timedelta(hours=REFRESH_TOKEN_DAYS), created_at=now)

    return response

@app.get("/api/v1/getuser", include_in_schema=False)
async def GetUser(session: str = Cookie(None)):
    """Attempts to get the currently logged in user"""
    try:
        user = get_current_user(session)
        return {
            'status': 1,
            'user': user["username"]
        }
    except:
        return {
            'status': 0,
            'user': "None"
        }

"""
Dashboard endpoints

Endpoints called by the dashboard
"""
@app.get("/api/v1/getEntries", tags=["Dashboard"])
async def GetEntries(count:int=50, user=Depends(get_current_user)):
    """
    Gets the next 'count' entries of the user.
    """
    async with httpx.AsyncClient() as client:
        # Search for items across collections, limited by the requested count 
        response = await client.get(STAC_URL+"/search", 
            params={
                "limit": count,
                "query": '{"properties.oam:uploaderid": {"eq": "'+user['sub']+'"}}'
                }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch entries")
        
        return {
            "processing": [uploaddb[id] for id in usertoupload[user['sub']]],
            "registered": response.json()
        }

class EditEntryBody(BaseModel):
    id: str
    edits: Dict[str, str]
@app.patch("/api/v1/editEntry", tags=["Dashboard"])
async def EditEntry(body: EditEntryBody, user=Depends(get_current_user)):
    """
    Edits a single entry
    """
    valid = {
        'license': lambda x: x if x in ["CC-BY 4.0","CC BY-NC 4.0","CC BY-SA 4.0"] else False, 
        'instruments': lambda x: [x], 
        'oam:platform_type': lambda x: x if x in ["satellite", "aircraft", "uav", "balloon", "kite"] else False, 
        'oam:producer_name': lambda x: x, 
        'contact': lambda x: x
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(STAC_URL+"/collections/openaerialmap/items/"+body.id)
        if response.status_code != 200:
            raise HTTPException(response.status_code)
        response = response.json()
        if response["properties"]["oam:uploaderid"] != user['sub']:
            raise HTTPException(401)
        for key in body.edits.keys():
            if key in valid and valid[key](body.edits[key]):
                response["properties"][key] = valid[key](body.edits[key])
        response = await client.patch(STAC_URL+"/collections/openaerialmap/items/"+body.id, json=response)
        if response.status_code != 200:
            raise HTTPException(response.status_code)
        return 200

@app.delete("/api/v1/deleteentry", tags=["Dashboard"])
async def DeleteEntry(id:str, user=Depends(get_current_user)):
    """
    Deletes the specified entry
    TODO: DELETE ASSOCIATED AWS S3 INFORMATION
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(STAC_URL+"/collections/openaerialmap/items/"+id)
        if response.status_code != 200:
            raise HTTPException(response.status_code)
        if response.json()["properties"]["oam:uploaderid"] != user['sub']:
            raise HTTPException(401)
        response = await client.delete(STAC_URL+"/collections/openaerialmap/items/"+id)
        if response.status_code != 200:
            raise HTTPException(response.status_code)
        return 200

"""
AWS S3 Endpoints
"""
class createmultipartBody(BaseModel):
    filename: str
    metadata: Dict[str, str]
    contenttype: str
@app.post("/api/v1/s3/createmultipart", tags=["AWS S3"])
async def createmultipart(body: createmultipartBody, user=Depends(get_current_user)):
    """
    Creates a multipart upload
    """
    userid = user["sub"]
    key = userid+"/"+slugify(body.metadata["title"])+"/"+body.filename
    try:
        s3.head_object(Bucket=S3BUCKET, Key=key)
        raise HTTPException(400, "Dataset of the same title already exists!")
    except botocore.exceptions.ClientError:
        pass
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
async def abortmultipart(body: abortmultipartBody, _=Depends(get_current_user)):
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
async def completemultipart(body: completemultipartBody, user=Depends(get_current_user)):
    try:
        parts = [
            {
                "ETag": p.ETag,
                "PartNumber": p.PartNumber
            }
            for p in body.parts
        ]

        path = body.key.split("/")
        folder = path[:-1]
        file = path[-1]
        folder = "s3://"+S3BUCKET+"/"+"/".join(folder)+"/"
        argo = invoke_processing(s3_path=folder, filename=file, key=body.key, userid=user['sub'])['metadata']['name']
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
async def signedurl(body: signedurlBody, _=Depends(get_current_user)):
    """
    Generates a presigned URL for multipart upload
    """
    if(not (0 < body.partnumber <= 10000)):
        raise HTTPException(status_code=400, detail="partnumber must be 1-10,000 (inclusive)!")
    external = boto3.client(
        "s3",
        endpoint_url=os.getenv("EXTERNAL_S3_ENDPOINT", "http://localhost:4566"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    params = {
        'Bucket': S3BUCKET,
        'Key': body.key,
        'PartNumber': body.partnumber,
        'UploadId': body.uploadid
    }
    try:
        url = external.generate_presigned_url(ClientMethod="upload_part", Params=params, ExpiresIn=3600)
        return {
            'url': url
        }
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])

class listpartsBody(BaseModel):
    key: str
    uploadid: str
@app.post("/api/v1/s3/listparts", tags=["AWS S3"])
async def listparts(body: listpartsBody, _=Depends(get_current_user)):
    """
    Returns the parts of a multipartupload that have already been uploaded
    """
    try:
        return s3.list_parts(Bucket=S3BUCKET, Key=body.key, UploadId=body.uploadid).get("Parts", [])
    except botocore.exceptions.ClientError as err:
        raise HTTPException(status_code=400, detail=err.response['Error']['Message'])
    except KeyError as err: # The parts key will not exist if no parts have been uploaded
        raise HTTPException(status_code=400, detail="No parts uploaded!")

"""
Static file serving
"""
STATICP = Path(__file__).parent / "static/public"
STATICA = Path(__file__).parent / "static/authorized"
@app.get("{full_path:path}", include_in_schema=False)
async def ServeHTML(full_path: str, session: str = Cookie(None)):
    """
    Serves static web files (HTML, CSS, etc.)
    """
    if full_path == "/" or full_path == "":
        full_path = "index.html"
    elif ".css" in full_path or ".js" in full_path:
        full_path = "."+full_path
    else:
        full_path = "."+full_path+".html"
    fileP = STATICP / full_path
    fileA = STATICA / full_path
    if fileP.exists():
        return FileResponse(fileP)
    if fileA.exists():
        try:
            get_current_user(session)
        except HTTPException:
            return RedirectResponse("/401")
        return FileResponse(fileA)
    else:
        return RedirectResponse("/404")