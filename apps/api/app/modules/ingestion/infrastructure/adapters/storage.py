"""FileStorage over the S3-compatible object store (MinIO)."""
from app.shared.infrastructure import storage


class S3FileStorage:
    def put(self, key: str, data: bytes, content_type: str) -> None:
        storage.put(key, data, content_type)

    def get(self, key: str) -> tuple[bytes, str]:
        return storage.get(key)

    def delete(self, key: str) -> None:
        try:
            storage.client().delete_object(Bucket=storage.get_settings().s3_bucket, Key=key)
        except Exception:  # cleanup is best effort: an orphan object is only garbage
            pass
