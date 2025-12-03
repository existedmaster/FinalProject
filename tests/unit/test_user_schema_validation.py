import pytest
from pydantic import ValidationError

from app.schemas.user import PasswordUpdate, UserCreate


@pytest.mark.parametrize(
    "password, error_msg",
    [
        ("Short1!", "String should have at least 8 characters"),
        ("alllowercase1!", "Password must contain at least one uppercase letter"),
        ("ALLUPPERCASE1!", "Password must contain at least one lowercase letter"),
        ("NoDigits!!", "Password must contain at least one digit"),
        ("NoSpecial123", "Password must contain at least one special character"),
    ],
)
def test_user_create_password_strength(password, error_msg):
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            username="testuser",
            password=password,
            confirm_password=password,
        )
    assert error_msg in str(exc.value)


def test_user_create_password_mismatch():
    with pytest.raises(ValidationError) as exc:
        UserCreate(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            username="testuser",
            password="SecurePass123!",
            confirm_password="Mismatch123!",
        )
    assert "Passwords do not match" in str(exc.value)


def test_password_update_validator_errors():
    with pytest.raises(ValidationError) as exc:
        PasswordUpdate(
            current_password="OldPass123!",
            new_password="OldPass123!",
            confirm_new_password="OldPass123!",
        )
    assert "New password must be different from current password" in str(exc.value)

    with pytest.raises(ValidationError) as exc2:
        PasswordUpdate(
            current_password="OldPass123!",
            new_password="NewPass123!",
            confirm_new_password="Mismatch123!",
        )
    assert "New password and confirmation do not match" in str(exc2.value)

    weak_passwords = [
        ("short1!", "at least 8 characters"),
        ("alllowercase1!", "uppercase"),
        ("ALLUPPERCASE1!", "lowercase"),
        ("NoDigits!!", "digit"),
        ("NoSpecial123", "special character"),
    ]
    for pwd, snippet in weak_passwords:
        with pytest.raises(ValidationError) as exc3:
            PasswordUpdate(
                current_password="OldPass123!",
                new_password=pwd,
                confirm_new_password=pwd,
            )
        assert snippet in str(exc3.value)
