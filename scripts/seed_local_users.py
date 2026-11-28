"""Seed local development accounts (admin and student) into PostgreSQL."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from src.acdp.api.db.models import User
from src.acdp.api.db.postgres import async_session_factory
from src.acdp.api.security import hash_password

LOCAL_ACCOUNTS: list[tuple[str, str, str, str]] = [
    ("admin@acdp.dev", "adminadmin", "admin", "Admin Local"),
    ("user@acdp.dev", "useruser", "student", "User Local"),
]


async def seed_local_users() -> None:
    """Create default local admin and student accounts if they do not exist."""
    async with async_session_factory() as db:
        for email, password, role, full_name in LOCAL_ACCOUNTS:
            existing = (
                await db.execute(select(User).where(User.email == email))
            ).scalar_one_or_none()
            if existing is None:
                db.add(
                    User(
                        email=email,
                        password_hash=hash_password(password),
                        role=role,
                        full_name=full_name,
                    )
                )
                print(f"Created {email} ({role})")
            else:
                existing.password_hash = hash_password(password)
                print(f"Updated password for {email} ({existing.role})")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_local_users())
