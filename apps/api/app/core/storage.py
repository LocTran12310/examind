import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings


def client():
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint,
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
        region_name="us-east-1",
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def ensure_bucket() -> None:
    s = get_settings()
    c = client()
    try:
        c.head_bucket(Bucket=s.s3_bucket)
    except ClientError:
        c.create_bucket(Bucket=s.s3_bucket)


def healthy() -> bool:
    try:
        ensure_bucket()
        return True
    except (BotoCoreError, ClientError):
        return False


def put(key: str, data: bytes, content_type: str) -> None:
    client().put_object(Bucket=get_settings().s3_bucket, Key=key, Body=data, ContentType=content_type)


def get(key: str) -> tuple[bytes, str]:
    obj = client().get_object(Bucket=get_settings().s3_bucket, Key=key)
    return obj["Body"].read(), obj.get("ContentType", "application/octet-stream")
