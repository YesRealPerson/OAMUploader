"""
(1)
Creates working directory and downloads file
"""
import boto3
import os
from dotenv import load_dotenv

if(not os.getenv("PRODUCTION")):
    load_dotenv()

S3BUCKET = os.getenv("BUCKET_NAME")
# Amazon s3 session
session = boto3.Session()
s3 = boto3.client('s3')
if(len(s3.list_buckets()["Buckets"]) == 0):
    raise ValueError("AWS S3 has zero buckets!")