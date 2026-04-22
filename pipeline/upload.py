"""
(5)
Upload COG and sidecar files to OIN S3 bucket
Create STAC Item and register with pgSTAC via API
Update upload status and notify user
"""
import boto3

def upload_cog_multipart(file_path, bucket_name, object_key):
    s3 = boto3.client("s3")

    response = s3.create_multipart_upload(Bucket=bucket_name, Key=object_key)
    upload_id = response["UploadId"]
    parts = []
    part_number = 1
    chunk_size = 5242880  

    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            part = s3.upload_part(Bucket=bucket_name, Key=object_key, PartNumber=part_number, UploadId=upload_id, Body=data)
            parts.append({"PartNumber": part_number, "ETag": part["ETag"]})
            part_number += 1

    s3.complete_multipart_upload(Bucket=bucket_name, Key=object_key, UploadId=upload_id, MultipartUpload={"Parts": parts})
    return "cog to S3 upload complete"
