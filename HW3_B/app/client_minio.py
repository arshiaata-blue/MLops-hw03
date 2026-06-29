"""app.client_minio — MinIO client (used only for bundle download in s3 mode)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from . import config


# TODO: implement get_credentials() -> dict
# Return a dict with endpoint, access_key, secret_key, bucket, prefix
# Read MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_PREFIX from env
# HINT: use os.getenv() with sensible defaults
# HINT: prefix should include STUDENT_USERNAME, e.g. f"{config.STUDENT_USERNAME}/"
def get_credentials() -> dict:
    endpoint = os.getenv("MINIO_ENDPOINT", "185.50.38.163:33333")
    access_key = os.getenv("MINIO_ACCESS_KEY", f"qbc12-{config.STUDENT_USERNAME}")
    secret_key = os.getenv("MINIO_SECRET_KEY", "")
    bucket = os.getenv("MINIO_BUCKET", "hw03-bundles")
    prefix = os.getenv("MINIO_PREFIX", f"{config.STUDENT_USERNAME}/")
    
    return {
        "endpoint": endpoint,
        "access_key": access_key,
        "secret_key": secret_key,
        "bucket": bucket,
        "prefix": prefix
    }


# TODO: implement download_bundle(target_dir: Path) -> bool
# Pull the bundle from MinIO into target_dir. Returns True on success.
# Only used in MODEL_SOURCE=s3 mode.
# HINT: from minio import Minio
# HINT: client = Minio(endpoint, access_key=..., secret_key=..., secure=False)
# HINT: target_dir.mkdir(parents=True, exist_ok=True)
# HINT: iterate client.list_objects(bucket, prefix=prefix, recursive=True)
# HINT: for each obj, compute rel = obj.object_name[len(prefix):], skip if not rel or obj.is_dir
# HINT: dest = target_dir / rel; dest.parent.mkdir(parents=True, exist_ok=True)
# HINT: client.fget_object(bucket, obj.object_name, str(dest))
# HINT: return True on success, False on any exception
def download_bundle(target_dir: Path) -> bool:
    try:
        from minio import Minio
        
        creds = get_credentials()
        endpoint = creds["endpoint"]
        access_key = creds["access_key"]
        secret_key = creds["secret_key"]
        bucket = creds["bucket"]
        prefix = creds["prefix"]
        
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        objects = client.list_objects(bucket, prefix=prefix, recursive=True)
        for obj in objects:
            if obj.is_dir:
                continue
                
            object_name = obj.object_name
            if not object_name.startswith(prefix):
                continue
                
            rel = object_name[len(prefix):]
            if not rel or rel.strip() == "":
                continue
                
            dest = target_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            client.fget_object(bucket, object_name, str(dest))
            
        return True
    except Exception:
        return False