#!/usr/bin/env python3

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tortoise import Tortoise
from src.core.config import settings, tortoise_config
from src.models.models import User
from src.enums import UserRole
from src.api.auth.password_manager import PasswordManager


async def create_default_users():
    try:
        await create_admin()
        await create_staff()
        await create_user()
    except Exception as e:
        print(f"Failed to create default users: {e}")
        raise


async def create_admin():
    admin_exists = await User.filter(role=UserRole.ADMIN).exists()
    if admin_exists:
        return

    hashed_password = PasswordManager.hash_password(settings.initial_admin_password)

    admin = await User.create(
        email=settings.initial_admin_email,
        password_hash=hashed_password,
        role=UserRole.ADMIN
    )

    print(f"Default admin created: {settings.initial_admin_email} (ID: {admin.display_id})")


async def create_staff():
    staff_exists = await User.filter(email=settings.initial_staff_email).exists()
    if staff_exists:
        return

    hashed_password = PasswordManager.hash_password(settings.initial_staff_password)

    staff = await User.create(
        email=settings.initial_staff_email,
        password_hash=hashed_password,
        role=UserRole.STAFF
    )

    print(f"Default staff created: {settings.initial_staff_email} (ID: {staff.display_id})")


async def create_user():
    user_exists = await User.filter(email=settings.initial_user_email).exists()
    if user_exists:
        return

    hashed_password = PasswordManager.hash_password(settings.initial_user_password)

    user = await User.create(
        email=settings.initial_user_email,
        password_hash=hashed_password,
        role=UserRole.USER,
        inn="123456789012",
        phone="+7-900-123-4567",
        first_name="Test",
        last_name="User"
    )

    print(f"Default user created: {settings.initial_user_email} (ID: {user.display_id})")


async def main():
    try:
        await Tortoise.init(config=tortoise_config)
        await create_default_users()
    except Exception as e:
        print(f"Bootstrap failed: {e}")
        sys.exit(1)
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())