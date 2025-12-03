from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.main import (
    app,
    change_password,
    create_calculation,
    dashboard_page,
    delete_calculation,
    edit_calculation_page,
    get_calculation,
    list_calculations,
    login_json,
    login_page,
    read_current_user_profile,
    read_health,
    read_index,
    register,
    register_page,
    update_calculation,
    update_current_user_profile,
    view_calculation_page,
)
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationUpdate
from app.schemas.token import TokenResponse
from app.schemas.user import PasswordUpdate, UserCreate, UserLogin, UserResponse, UserUpdate


def _fake_request(path: str):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
        "app": app,
    }
    return Request(scope)


def _create_user(db_session, password: str = "SecurePass123!"):
    user_data = {
        "first_name": "Main",
        "last_name": "Tester",
        "email": f"{uuid4()}@example.com",
        "username": f"user_{uuid4()}",
        "password": password,
    }
    user = User.register(db_session, {**user_data, "password": password})
    db_session.commit()
    db_session.refresh(user)
    return user, password


def _user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user, from_attributes=True)


def test_web_routes(db_session):
    for view in [read_index, login_page, register_page, dashboard_page]:
        resp = view(_fake_request("/"))
        assert resp.status_code == 200

    profile_resp = view_calculation_page(_fake_request("/dashboard/view/1"), "123")
    assert profile_resp.status_code == 200

    edit_resp = edit_calculation_page(_fake_request("/dashboard/edit/1"), "123")
    assert edit_resp.status_code == 200


def test_register_and_login(db_session):
    payload = UserCreate(
        first_name="Flow",
        last_name="Tester",
        email=f"{uuid4()}@example.com",
        username=f"user_{uuid4()}",
        password="SecurePass123!",
        confirm_password="SecurePass123!",
    )
    registered = register(payload, db_session)
    assert registered.email == payload.email

    login_payload = UserLogin(username=payload.username, password=payload.password)
    login_result: TokenResponse = login_json(login_payload, db_session)
    assert login_result.username == payload.username
    assert login_result.access_token

    with pytest.raises(HTTPException):
        login_json(UserLogin(username=payload.username, password="WrongPass123!"), db_session)

    with pytest.raises(HTTPException):
        register(payload, db_session)


def test_profile_get_and_update(db_session):
    user, _ = _create_user(db_session)
    fetched = read_current_user_profile(current_user=user)
    assert fetched.id == user.id

    updates = UserUpdate(first_name="Updated", last_name="Name", email=f"{uuid4()}@example.com")
    updated = update_current_user_profile(updates, current_user=user, db=db_session)
    assert updated.first_name == "Updated"
    assert updated.last_name == "Name"


def test_change_password_logic(db_session):
    user, original_password = _create_user(db_session)

    with pytest.raises(HTTPException):
        change_password(
            PasswordUpdate(
                current_password="WrongPass123!",
                new_password="NewPass123!",
                confirm_new_password="NewPass123!",
            ),
            current_user=user,
            db=db_session,
        )

    change_password(
        PasswordUpdate(
            current_password=original_password,
            new_password="NewPass123!",
            confirm_new_password="NewPass123!",
        ),
        current_user=user,
        db=db_session,
    )

    assert user.verify_password("NewPass123!")


def test_calculation_crud_via_api(db_session):
    user, _ = _create_user(db_session)
    current = _user_response(user)

    created = create_calculation(
        CalculationBase(type="addition", inputs=[1, 2, 3]), current_user=current, db=db_session
    )
    assert isinstance(created, Calculation)
    assert created.result == 6

    listed = list_calculations(current_user=current, db=db_session)
    assert any(calc.id == created.id for calc in listed)

    fetched = get_calculation(str(created.id), current_user=current, db=db_session)
    assert fetched.id == created.id

    updated = update_calculation(
        str(created.id),
        CalculationUpdate(inputs=[10, 5]),
        current_user=current,
        db=db_session,
    )
    assert updated.result == 15

    delete_calculation(str(created.id), current_user=current, db=db_session)
    with pytest.raises(HTTPException):
        get_calculation(str(created.id), current_user=current, db=db_session)

    with pytest.raises(HTTPException):
        get_calculation("not-a-uuid", current_user=current, db=db_session)


def test_health_check():
    assert read_health() == {"status": "ok"}
