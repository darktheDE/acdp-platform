"""Tests for /api/v1/auth/* and /api/v1/bookmarks/* (Argon2id, rotation, EC-A2, EC-A3)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_auth_register_login_refresh_rotation_and_reuse_detection(api_client: AsyncClient) -> None:
    email = f"test_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
    password = "StrongPassword123!"

    reg = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Nguyen Van Test",
            "password": password,
            "student_or_staff_id": "23110086",
        },
    )
    assert reg.status_code == 201
    assert reg.json()["email"] == email

    # Duplicate email returns 409
    dup = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Dup", "password": password},
    )
    assert dup.status_code == 409

    # Login sets HttpOnly refresh cookie and returns access JWT
    login = await api_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    access_token = login.json()["access_token"]
    old_refresh_cookie = login.cookies.get("acdp_refresh_token")
    assert old_refresh_cookie

    # /me succeeds with Bearer JWT
    me = await api_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    assert me.json()["student_or_staff_id"] == "23110086"

    # Refresh rotates token
    ref = await api_client.post("/api/v1/auth/refresh", cookies={"acdp_refresh_token": old_refresh_cookie})
    assert ref.status_code == 200
    new_refresh_cookie = ref.cookies.get("acdp_refresh_token")
    assert new_refresh_cookie and new_refresh_cookie != old_refresh_cookie

    # Reusing the revoked old refresh cookie must fail (401) and revoke active sessions
    reused = await api_client.post("/api/v1/auth/refresh", cookies={"acdp_refresh_token": old_refresh_cookie})
    assert reused.status_code == 401

    revoked_new = await api_client.post("/api/v1/auth/refresh", cookies={"acdp_refresh_token": new_refresh_cookie})
    assert revoked_new.status_code == 401


@pytest.mark.anyio
async def test_bookmarks_idempotency_and_cross_user_isolation(api_client: AsyncClient) -> None:
    comp_resp = await api_client.get("/api/v1/competitions", params={"page_size": 1})
    comp_key = comp_resp.json()["items"][0]["competition_key"]

    async def _create_and_login() -> str:
        em = f"test_{uuid.uuid4().hex[:8]}@hcmute.edu.vn"
        pw = "SecretPass123!"
        await api_client.post("/api/v1/auth/register", json={"email": em, "full_name": "User", "password": pw})
        r = await api_client.post("/api/v1/auth/login", json={"email": em, "password": pw})
        return r.json()["access_token"]

    token_a = await _create_and_login()
    token_b = await _create_and_login()
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Save bookmark twice -> idempotent (EC-A3)
    b1 = await api_client.post(
        "/api/v1/bookmarks",
        json={"competition_key": comp_key, "personal_note": "Lap nhom 3 nguoi"},
        headers=headers_a,
    )
    assert b1.status_code == 201
    b2 = await api_client.post(
        "/api/v1/bookmarks",
        json={"competition_key": comp_key, "personal_note": "Cap nhat ghi chu"},
        headers=headers_a,
    )
    assert b2.status_code == 201
    assert b2.json()["personal_note"] == "Cap nhat ghi chu"

    list_a = await api_client.get("/api/v1/bookmarks", headers=headers_a)
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["is_archived"] is False

    # User B cannot see or delete User A's bookmark
    list_b = await api_client.get("/api/v1/bookmarks", headers=headers_b)
    assert list_b.json() == []
    del_b = await api_client.delete(f"/api/v1/bookmarks/{comp_key}", headers=headers_b)
    assert del_b.status_code == 404

    # User A deletes own bookmark
    del_a = await api_client.delete(f"/api/v1/bookmarks/{comp_key}", headers=headers_a)
    assert del_a.status_code == 204
