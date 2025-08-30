import os
import json
import requests, datetime, hashlib, hmac
import requests
import hashlib
import hmac
from urllib.parse import quote
import xml.etree.ElementTree as ET
import hashlib

ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
SECRET_KEY = os.environ.get('S3_SECRET_KEY')
HOST = os.environ.get('S3_HOST')



MIME_TYPES = {
    # Images
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "svg": "image/svg+xml",

    # Documents
    "pdf": "application/pdf",
    "txt": "text/plain",
    "rtf": "application/rtf",
    "html": "text/html",
    "htm": "text/html",
    "xml": "application/xml",
    "csv": "text/csv",
    "json": "application/json",

    # Microsoft Office
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    # Archives / Compressed
    "zip": "application/zip",
    "tar": "application/x-tar",
    "gz": "application/gzip",
    "bz2": "application/x-bzip2",
    "7z": "application/x-7z-compressed",

    # Audio
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "m4a": "audio/mp4",

    # Video
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "wmv": "video/x-ms-wmv",
    "flv": "video/x-flv",
    "mkv": "video/x-matroska",

    # Programing
    "css": "text/css",
    "js": "text/javascript",

}


# -----------------
# Config
# -----------------
access_key = ACCESS_KEY
secret_key = SECRET_KEY
region = "us-east-1"
service = "s3"
bucket = "test3"
endpoint = f"https://{HOST}"

def utc_midnight():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    current_utc_date = utc_now.date()
    midnight_time = datetime.time(0, 0, 0)
    return datetime.datetime.combine(current_utc_date, midnight_time).replace(tzinfo=datetime.timezone.utc)

# -----------------
# Signature V4 Helpers
# -----------------
def sign(key, msg):
    return hmac.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region, service):
    kDate = sign("AWS4" + key, date_stamp)
    kRegion = hmac.new(kDate, region.encode("utf-8"), hashlib.sha256).digest()
    kService = hmac.new(kRegion, service.encode("utf-8"), hashlib.sha256).digest()
    kSigning = hmac.new(kService, b"aws4_request", hashlib.sha256).digest()
    return kSigning

def aws_request(method, bucket, query="", body=""):
    host = HOST
    canonical_uri = f"/{bucket}"
    canonical_querystring = query

    t = datetime.datetime.now(datetime.timezone.utc)
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")

    payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    canonical_headers = (
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )

    signed_headers = "host;x-amz-content-sha256;x-amz-date"

    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        f"{algorithm}\n{amz_date}\n{credential_scope}\n" +
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    )

    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization_header = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Authorization": authorization_header,
    }

    url = f"{endpoint}/{bucket}"
    url = f'{url}?{query}' if query else url
    if method == "PUT":
        if body:
            r = requests.put(url, data=body, headers=headers)
        else:
            r = requests.put(url, headers=headers)
        print(r.status_code, r.text)
    else:
        r = requests.get(url, headers=headers)
        print(r.status_code, r.text)
    return r

def get_canon_query(q: dict) -> str:
    # Sort by key, then value; encode names and values per RFC 3986
    items = []
    for k in sorted(q.keys()):
        v = q[k]
        if isinstance(v, (list, tuple)):
            for val in sorted(v):
                items.append(f"{quote(str(k), safe="-_.~")}={quote(str(v), safe="-_.~")}")
        else:
            items.append(f"{quote(str(k), safe="-_.~")}={quote(str(v), safe="-_.~")}")
    return "&".join(items)

def generate_presigned_url( bucket, object_key, region="us-east-1", method="GET", expires=3600 * 24, scheme="https", params=None):
    service = "s3"

    # Dates
    # now = datetime.datetime.now(datetime.timezone.utc)
    now = utc_midnight()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    signed_host = HOST
    if object_key:
        canonical_uri = f"/{bucket}/{object_key}"
    else:
        canonical_uri = f"/{bucket}"

    # Query params (DO NOT pre-encode; we will encode once, in get_canon_query)
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    query = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{ACCESS_KEY}/{credential_scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
    }
    if object_key and object_key.startswith('static/'):
        query["X-Amz-ACL"] = 'public-read'
    if params: query.update(**params)
    session_token = None
    if session_token:
        query["X-Amz-Security-Token"] = session_token

    # Canonical request
    canonical_headers = f"host:{signed_host}\n"
    signed_headers = "host"
    payload_hash = "UNSIGNED-PAYLOAD"

    canonical_query = get_canon_query(query)
    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_query}\n"
        f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    # String to sign
    string_to_sign = (
        "AWS4-HMAC-SHA256\n"
        f"{amz_date}\n{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
    )

    # Signature
    signing_key = get_signature_key(SECRET_KEY, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # Final URL (rebuild query including signature, sorted & encoded)
    query["X-Amz-Signature"] = signature
    final_query = get_canon_query(query)
    return f"{scheme}://{signed_host}{canonical_uri}?{final_query}"

def put_object(bucket, object_key=None, object_data=None):
    headers = {}
    if object_key and '.' in object_key:
        headers["Content-Type"] = MIME_TYPES[object_key.split('.')[-1].lower()]
    url = generate_presigned_url(bucket=bucket, object_key=object_key, method="PUT")
    print("PUT:",  url)
    resp = requests.put( url, data=object_data, headers=headers)
    print("Response", resp.status_code, resp.text)

def get_object(bucket, object_key=None, only_url=False):
    url = generate_presigned_url(bucket=bucket, object_key=object_key, method="GET")
    if only_url:
        print("GET:",  url)
        return url
    else:
        resp = requests.get( url)
        print("Response", resp.status_code)
        if resp.status_code == 200:
            return resp.content
        elif resp.status_code == 404:
            return None
        else:
            raise Exception(resp.text)
        
def delete_object(bucket, object_key=None):
    url = generate_presigned_url(bucket=bucket, object_key=object_key, method="DELETE")
    print("DELETE:",  url)
    resp = requests.delete(url)
    print("Response", resp.status_code, resp.text)
    if resp.status_code == 204:
        return True
    else:
        raise Exception(resp.text)


def list_objects(bucket, prefix='', max_keys=1000):
    files = {}
    params = {'list-type': '2', 'prefix': prefix, 'max-keys': max_keys}
    url = generate_presigned_url(bucket=bucket, object_key=None, method="GET", params=params)
    print("GET URL:",  url)
    resp = requests.get( url)
    print("Response", resp.status_code)
    if resp.status_code == 200:
        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
        root = ET.fromstring(resp.text)
        files = {}
        for content in root.findall("s3:Contents", ns):
            key = content.find("s3:Key", ns).text
            etag = content.find("s3:ETag", ns).text[1:-1]
            # last_modified = content.find("s3:LastModified", ns).text
            files[key] = etag
        return files
    elif resp.status_code == 404:
        return files
    else:
        raise Exception(resp.text)

def md5(filepath, chunk_size=8192):
    """Calculates the MD5 hash of a given file."""
    md5_hash = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except FileNotFoundError:
        return "File not found."


def policy(bucket):
    return json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/static/*"]
            }
        ]
    })

if __name__ == "__main__":

    object_key = 'hello.txt'

    aws_request("PUT", bucket)
    aws_request("PUT", bucket, "policy=", policy())
    aws_request("GET", bucket, "policy=")

    hash = md5(object_key)
    print(hash)

    with open(object_key, 'rb') as file:
        put_object(bucket, object_key, file.read())

    get_object(bucket, object_key, only_url=True)
    content = get_object(bucket, object_key)
    print(content)

    files = list_objects(bucket, '')
    print(files)
    assert files['hello.txt'] == hash
