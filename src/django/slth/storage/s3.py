import os
import json
import requests, datetime, hashlib, hmac
import requests
import hashlib
import hmac
from urllib.parse import quote
import xml.etree.ElementTree as ET
import hashlib
from urllib.parse import urlparse


ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
SECRET_KEY = os.environ.get('S3_SECRET_KEY')
HOST = os.environ.get('S3_HOST')

ACCESS_KEY = "005bde91dfe20520000000001"
SECRET_KEY = "K005whTk47psOkSUAICKFa0A6lHrOjk"
HOST = 's3.us-east-005.backblazeb2.com'

ACCESS_KEY = "2298084ef1d15932dc6a57ce219e2c1a"
SECRET_KEY = "abef8c02f20552daa61f30704ccb8e46f7762587507e745ce79a7c436d6c313a"
HOST = '29e028e0627d615d399ba209175a5ef8.r2.cloudflarestorage.com'

ACCESS_KEY = "admin"
SECRET_KEY = "1793ifrn.?"
HOST = 'api.minio.aplicativo.click'

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


class Client:

    
    def __init__(self, url, access_key, secret_key, auto_create=False):
        prefix, suffix = url.split('://')
        host, bucket = suffix.split('/')
        self.scheme = prefix
        self.access_key = access_key
        self.secret_key = secret_key
        self.host = host
        self.bucket = bucket

        self.url = url
        self.region = "us-east-1"
        self.service = "s3"
        self.endpoint = f"{self.scheme}://{self.host}"

        if auto_create and not self.list_objects(self.bucket):
            self.create_bucket()
            self.set_policy()

    def create_bucket(self):
        self.aws_request("PUT")

    def set_policy(self):
        policy = json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/static/*"]
                }
            ]
        })
        self.aws_request("PUT", "policy=", policy)

    def get_policy(self):
        return self.aws_request("GET", "policy=")
    
    def get_signature_key(self, key, date_stamp):
        kDate = sign("AWS4" + key, date_stamp)
        kRegion = hmac.new(kDate, self.region.encode("utf-8"), hashlib.sha256).digest()
        kService = hmac.new(kRegion, self.service.encode("utf-8"), hashlib.sha256).digest()
        kSigning = hmac.new(kService, b"aws4_request", hashlib.sha256).digest()
        return kSigning


    def aws_request(self, method, query="", body=""):
        canonical_uri = f"/{self.bucket}"
        canonical_querystring = query

        t = datetime.datetime.now(datetime.timezone.utc)
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = t.strftime("%Y%m%d")

        payload_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

        canonical_headers = (
            f"host:{self.host}\n"
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
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n" +
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        )

        signing_key = self.get_signature_key(self.secret_key, date_stamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
            "Authorization": authorization_header,
        }

        url = f"{self.endpoint}/{self.bucket}"
        url = f'{url}?{query}' if query else url
        if method == "PUT":
            if body:
                r = requests.put(url, data=body, headers=headers)
            else:
                r = requests.put(url, headers=headers)
            print(r.status_code, r.text)
        else:
            r = requests.get(url, headers=headers, timeout=5)
            print(r.status_code, r.text)
        return r
    

    def generate_presigned_url(self, object_key, method="GET", expires=3600 * 24, scheme="https", params=None, source_object_key=None):
        service = "s3"

        # Dates
        # now = datetime.datetime.now(datetime.timezone.utc)
        now = utc_midnight()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        datestamp = now.strftime("%Y%m%d")
        signed_host = HOST
        if object_key:
            canonical_uri = f"/{self.bucket}/{object_key}"
        else:
            canonical_uri = f"/{self.bucket}"

        # Query params (DO NOT pre-encode; we will encode once, in get_canon_query)
        credential_scope = f"{datestamp}/{self.region}/{service}/aws4_request"
        query = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{ACCESS_KEY}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires),
            "X-Amz-SignedHeaders": "host",
        }
        if object_key and object_key.startswith('static/'):
            query["X-Amz-ACL"] = 'public-read'
        if source_object_key:
            query["X-Amz-Copy-Source"] = source_object_key
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
        signing_key = self.get_signature_key(SECRET_KEY, datestamp)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # Final URL (rebuild query including signature, sorted & encoded)
        query["X-Amz-Signature"] = signature
        final_query = get_canon_query(query)
        return f"{scheme}://{signed_host}{canonical_uri}?{final_query}"

    def put_object(self, object_key=None, object_data=None):
        headers = {}
        if object_key and '.' in object_key:
            headers["Content-Type"] = MIME_TYPES[object_key.split('.')[-1].lower()]
        url = self.generate_presigned_url(object_key=object_key, method="PUT")
        print("PUT:",  url)
        resp = requests.put( url, data=object_data, headers=headers)
        print("Response", resp.status_code, resp.text)

    def copy_object(self, source_object_key, target_object_key):
        source_object_key = f'/{self.bucket}/{source_object_key}'
        headers = {
            "x-amz-copy-source": source_object_key
        }
        url = self.generate_presigned_url(object_key=target_object_key, method="PUT", source_object_key=source_object_key)
        print("PUT:",  url)
        resp = requests.put(url, headers=headers)
        print("Response", resp.status_code, resp.text)

    def get_object(self, object_key=None, only_url=False):
        url = self.generate_presigned_url(object_key=object_key, method="GET")
        if only_url:
            print("GET:",  url)
            return url
        else:
            resp = requests.get(url, timeout=5)
            print("Response", resp.status_code)
            if resp.status_code == 200:
                return resp.content
            elif resp.status_code == 404:
                return None
            else:
                raise Exception(resp.text)
        
    def delete_object(self, object_key=None):
        url = self.generate_presigned_url(object_key=object_key, method="DELETE")
        print("DELETE:",  url)
        resp = requests.delete(url)
        print("Response", resp.status_code, resp.text)
        if resp.status_code == 204:
            return True
        else:
            raise Exception(resp.text)

    def list_objects(self, prefix='', max_keys=1000):
        files = {}
        params = {'list-type': '2', 'prefix': prefix, 'max-keys': max_keys}
        url = self.generate_presigned_url(object_key=None, method="GET", params=params)
        print("GET URL:",  url)
        resp = requests.get(url, timeout=5)
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


if __name__ == "__main__":

    object_key = 'hello.txt'
    hash = md5(object_key)

    s3 = Client('https://api.minio.aplicativo.click/test3', 'admin', '1793ifrn.?')
    s3.create_bucket()
    s3.set_policy()
    s3.get_policy()
    
    with open(object_key, 'rb') as file:
        s3.put_object(object_key, file.read())

    url = s3.get_object(object_key, only_url=True)
    print(url)
    content = s3.get_object(object_key)
    print(content)

    files = s3.list_objects()
    print(files)
    assert files['hello.txt'] == hash
