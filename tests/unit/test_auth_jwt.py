from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.auth import jwt as jwt_module
from app.models.user import User
from app.schemas.token import TokenType
from tests.conftest import create_fake_user

pytestmark = pytest.mark.anyio("asyncio")

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
def stub_blacklist(monkeypatch):
    async def never_blacklisted(*args, **kwargs):
        return False

    monkeypatch.setattr(jwt_module, "is_blacklisted", never_blacklisted)


def test_create_token_handles_uuid_conversion():
    token = jwt_module.create_token(uuid4(), TokenType.ACCESS, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)


def test_create_token_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("encode failure")

    monkeypatch.setattr(jwt_module.jwt, "encode", boom)

    with pytest.raises(HTTPException) as exc:
        jwt_module.create_token("user", TokenType.ACCESS)

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.anyio
async def test_decode_token_type_mismatch():
    token = jwt_module.create_token("user", TokenType.REFRESH)
    with pytest.raises(HTTPException) as exc:
        await jwt_module.decode_token(token, TokenType.ACCESS)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.anyio
async def test_decode_token_revoked(monkeypatch):
    async def always_blacklisted(*args, **kwargs):
        return True

    monkeypatch.setattr(jwt_module, "is_blacklisted", always_blacklisted)
    token = jwt_module.create_token("user", TokenType.ACCESS)

    with pytest.raises(HTTPException) as exc:
        await jwt_module.decode_token(token, TokenType.ACCESS)
    assert "revoked" in exc.value.detail


@pytest.mark.anyio
async def test_decode_token_expired():
    token = jwt_module.create_token("user", TokenType.ACCESS, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc:
        await jwt_module.decode_token(token, TokenType.ACCESS)
    assert exc.value.detail == "Token has expired"


@pytest.mark.anyio
async def test_get_current_user_success(db_session):
    user_data = create_fake_user()
    plain_password = "ValidPass123!"
    user_data["password"] = User.hash_password(plain_password)
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = jwt_module.create_token(user.id, TokenType.ACCESS)
    current = await jwt_module.get_current_user(token=token, db=db_session)
    assert current.id == user.id


@pytest.mark.anyio
async def test_get_current_user_inactive(db_session):
    user_data = create_fake_user()
    user_data["password"] = User.hash_password("ValidPass123!")
    user_data["is_active"] = False
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = jwt_module.create_token(user.id, TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc:
        await jwt_module.get_current_user(token=token, db=db_session)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
