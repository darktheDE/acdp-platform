"""Tests for /api/v1/profile/* (Student Mini-CV, Option A URLs, Option B R2 PDF upload, privacy)."""

from __future__ import annotations

import uuid
from uuid import UUID

import pytest
from httpx import AsyncClient

from acdp.api.main import app
from acdp.api.services.cv_storage import MAX_CV_SIZE_BYTES, get_cv_storage_service


class FakeCvStorageService:
    """In-memory Cloudflare R2 stub for deterministic offline API tests."""

    def __init__(self, *, configured: bool = True) -> None:
        self._configured = configured
        self.objects: dict[str, bytes] = {}

    def is_configured(self) -> bool:
        return self._configured

    async def upload_pdf(self, user_id: UUID, content: bytes, filename: str) -> str:
        key = f"profiles/cv/{user_id}.pdf"
        self.objects[key] = content
        return key

    async def download_pdf(self, storage_key: str) -> bytes | None:
        return self.objects.get(storage_key)

    async def delete_pdf(self, storage_key: str) -> None:
        self.objects.pop(storage_key, None)


async def _register_and_login(
    client: AsyncClient,
    *,
    full_name: str = "Nguyen Van Hung",
    student_id: str | None = None,
) -> tuple[str, str]:
    email = f"test_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
    password = "StrongPassword123!"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": full_name,
            "password": password,
            "student_or_staff_id": student_id,
        },
    )
    assert reg.status_code == 201
    user_id = reg.json()["id"]
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    return user_id, login.json()["access_token"]


@pytest.mark.anyio
async def test_profile_requires_auth_and_defaults_for_new_student(api_client: AsyncClient) -> None:
    unauth = await api_client.get("/api/v1/profile/me")
    assert unauth.status_code == 401

    user_id, token = await _register_and_login(api_client, full_name="Tran Minh Test")
    resp = await api_client.get("/api/v1/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user_id
    assert data["full_name"] == "Tran Minh Test"
    assert data["skills"] == []
    assert data["has_uploaded_cv"] is False
    assert data["completeness_pct"] == 0
    assert len(data["missing_fields"]) == 8


@pytest.mark.anyio
async def test_profile_upsert_syncs_user_normalizes_skills_and_validates_urls(api_client: AsyncClient) -> None:
    _, token = await _register_and_login(api_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Reject unsafe javascript: or plain http:// URLs
    bad_url = await api_client.put(
        "/api/v1/profile/me",
        headers=headers,
        json={"cv_url": "javascript:alert(1)"},
    )
    assert bad_url.status_code == 422

    bad_http = await api_client.put(
        "/api/v1/profile/me",
        headers=headers,
        json={"github_url": "http://github.com/student"},
    )
    assert bad_http.status_code == 422

    # Valid Mini-CV update
    payload = {
        "full_name": "Do Kien Hung",
        "student_or_staff_id": "23133030",
        "faculty": "Khoa Công nghệ Thông tin",
        "major": "Kỹ thuật Dữ liệu",
        "academic_year": "K23",
        "phone": "0901234567",
        "bio": "Quan tâm Data Engineering và RAG Pipeline.",
        "skills": [" Python ", "python", "DuckDB", "SQL", ""],
        "preferred_roles": ["Data Engineer", "data engineer", "Team Leader"],
        "achievements_summary": "Top 10 Data Hack 2025",
        "cv_url": "https://drive.google.com/file/d/sample-cv/view",
        "github_url": "https://github.com/darktheDE",
        "linkedin_url": "https://linkedin.com/in/hungdk",
        "is_open_to_team": True,
    }
    put_resp = await api_client.put("/api/v1/profile/me", headers=headers, json=payload)
    assert put_resp.status_code == 200
    body = put_resp.json()
    assert body["full_name"] == "Do Kien Hung"
    assert body["student_or_staff_id"] == "23133030"
    assert body["skills"] == ["Python", "DuckDB", "SQL"]
    assert body["preferred_roles"] == ["Data Engineer", "Team Leader"]
    assert body["completeness_pct"] == 100
    assert body["missing_fields"] == []

    # Verify /api/v1/auth/me reflects synced full_name and student_or_staff_id
    me_resp = await api_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["full_name"] == "Do Kien Hung"
    assert me_resp.json()["student_or_staff_id"] == "23133030"


@pytest.mark.anyio
async def test_profile_pdf_upload_download_delete_and_privacy(api_client: AsyncClient) -> None:
    fake_storage = FakeCvStorageService(configured=True)
    app.dependency_overrides[get_cv_storage_service] = lambda: fake_storage
    try:
        user_a_id, token_a = await _register_and_login(api_client, student_id="23110001")
        _, token_b = await _register_and_login(api_client, student_id="23110002")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        await api_client.put(
            "/api/v1/profile/me",
            headers=headers_a,
            json={"phone": "0988777666", "major": "Kỹ thuật Dữ liệu"},
        )

        # Reject non-PDF magic bytes
        bad_file = await api_client.post(
            "/api/v1/profile/me/cv",
            headers=headers_a,
            files={"file": ("malware.pdf", b"#!/bin/sh\necho pwned", "application/pdf")},
        )
        assert bad_file.status_code == 400

        # Reject oversized file (> 2 MB)
        oversized = await api_client.post(
            "/api/v1/profile/me/cv",
            headers=headers_a,
            files={"file": ("huge.pdf", b"%PDF-1.4\n" + b"0" * MAX_CV_SIZE_BYTES, "application/pdf")},
        )
        assert oversized.status_code == 413

        # Valid PDF upload (Option B)
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        up_resp = await api_client.post(
            "/api/v1/profile/me/cv",
            headers=headers_a,
            files={"file": ("../../CV_Hung_2026.pdf", pdf_bytes, "application/pdf")},
        )
        assert up_resp.status_code == 200
        up_data = up_resp.json()
        assert up_data["has_uploaded_cv"] is True
        assert up_data["cv_filename"] == "CV_Hung_2026.pdf"
        assert up_data["cv_size_bytes"] == len(pdf_bytes)
        assert up_data["cv_download_path"] == f"/api/v1/profile/{user_a_id}/cv"

        # Stream uploaded PDF with nosniff header
        dl_resp = await api_client.get(f"/api/v1/profile/{user_a_id}/cv", headers=headers_b)
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"].startswith("application/pdf")
        assert dl_resp.headers["x-content-type-options"] == "nosniff"
        assert dl_resp.content == pdf_bytes

        # Cross-user privacy: Student B cannot see Student A's phone; owner A can
        pub_b = await api_client.get(f"/api/v1/profile/{user_a_id}", headers=headers_b)
        assert pub_b.status_code == 200
        assert pub_b.json()["phone"] is None
        assert pub_b.json()["has_uploaded_cv"] is True

        pub_a = await api_client.get(f"/api/v1/profile/{user_a_id}", headers=headers_a)
        assert pub_a.status_code == 200
        assert pub_a.json()["phone"] == "0988777666"

        # Delete uploaded PDF
        del_resp = await api_client.delete("/api/v1/profile/me/cv", headers=headers_a)
        assert del_resp.status_code == 200
        assert del_resp.json()["has_uploaded_cv"] is False
        assert del_resp.json()["cv_download_path"] is None

        missing_dl = await api_client.get(f"/api/v1/profile/{user_a_id}/cv", headers=headers_a)
        assert missing_dl.status_code == 404
    finally:
        app.dependency_overrides.pop(get_cv_storage_service, None)
