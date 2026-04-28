import json, os, sys, urllib.request, urllib.error
import os


def post(url, data):
    print("POST:",url)
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        print(f"  Error {e.code}: {e.read().decode()}", file=sys.stderr)
        raise

def register_stac(filename:str):
    with open(filename, 'r') as f:
        meta = json.load(f)
    props = meta.get("properties", {})
    if "datetime" not in props and ("start_datetime" in props or "end_datetime" in props):
          props["datetime"] = None
    post(os.environ.get("STAC_URL", "http://localhost:7777")+"/collections/"+os.environ.get("STAC_COLLECTION", "openaerialmap")+"/items", meta)

register_stac(sys.argv[1])
# py ./script.py C:\Users\Stephen\Desktop\OAMUploader\Repo\temporary\tester1\metadata.json