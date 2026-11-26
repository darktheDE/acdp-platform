"""Cloudflare R2 storage service for student PDF CVs (Option B, TASK-SRV-01)."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from uuid import UUID

import boto3
from botocore.exceptions import ClientError

from acdp.config import settings

MAX_CV_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
PDF_MAGIC_PREFIX = b"%PDF-"


def sanitize_pdf_filename(raw_name: str | None) -> str:
    """Strip path segments and unsafe characters, guaranteeing a .pdf filename."""
    base = Path(raw_name or "").name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" ._")
    if not cleaned:
        return "student-cv.pdf"
    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf"
    if len(cleaned) > 120:
        stem = cleaned[:-4][:116].rstrip(" ._") or "student-cv"
        cleaned = f"{stem}.pdf"
    return cleaned


class CvStorageService:
    """Async wrapper around boto3 S3 client for storing student PDF CVs on Cloudflare R2."""

    def __init__(self) -> None:
        self.endpoint_url = settings.aws_endpoint_url.strip()
        self.access_key_id = settings.aws_access_key_id.strip()
        self.secret_access_key = settings.aws_secret_access_key.strip()
        self.region_name = settings.aws_region.strip() or "auto"
        self.bucket_name = settings.bucket_name.strip()

    def is_configured(self) -> bool:
        """Return True when all required Cloudflare R2 S3 credentials are configured."""
        return bool(
            self.endpoint_url
            and self.access_key_id
            and self.secret_access_key
            and self.bucket_name
        )

    def _client(self):
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
        )

    def _put_sync(self, key: str, content: bytes, filename: str) -> None:
        client = self._client()
        client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content,
            ContentType="application/pdf",
            Metadata={"original_filename": filename},
        )

    def _get_sync(self, key: str) -> bytes | None:
        client = self._client()
        try:
            resp = client.get_object(Bucket=self.bucket_name, Key=key)
            return resp["Body"].read()
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"NoSuchKey", "404", "NotFound"}:
                return None
            raise

    def _delete_sync(self, key: str) -> None:
        client = self._client()
        try:
            client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code not in {"NoSuchKey", "404", "NotFound"}:
                raise

    async def upload_pdf(self, user_id: UUID, content: bytes, filename: str) -> str:
        """Upload validated PDF bytes to R2 under profiles/cv/{user_id}.pdf."""
        if not self.is_configured():
            raise RuntimeError("R2_NOT_CONFIGURED")
        storage_key = f"profiles/cv/{user_id}.pdf"
        await asyncio.to_thread(self._put_sync, storage_key, content, filename)
        return storage_key

    async def download_pdf(self, storage_key: str) -> bytes | None:
        """Download PDF bytes from R2, returning None if the object does not exist."""
        if not self.is_configured():
            raise RuntimeError("R2_NOT_CONFIGURED")
        return await asyncio.to_thread(self._get_sync, storage_key)

    async def delete_pdf(self, storage_key: str) -> None:
        """Delete an uploaded PDF from R2 if configured."""
        if not self.is_configured():
            return
        await asyncio.to_thread(self._delete_sync, storage_key)


def get_cv_storage_service() -> CvStorageService:
    """FastAPI dependency returning the Cloudflare R2 CV storage service."""
    return CvStorageService()
