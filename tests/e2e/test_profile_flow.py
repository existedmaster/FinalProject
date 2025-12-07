from uuid import uuid4

import requests


def _register_user(base_url: str, username: str, email: str, password: str):
    resp = requests.post(
        f"{base_url}/auth/register",
        json={
            "first_name": "Flow",
            "last_name": "Tester",
            "email": email,
            "username": username,
            "password": password,
            "confirm_password": password,
        },
        timeout=10,
    )
    assert resp.status_code == 201, resp.text


def test_login_profile_password_change_and_relogin(fastapi_server: str, page):
    """
    Positive UI flow: change password then re-login with the new credentials.
    """
    base_url = fastapi_server.rstrip("/")
    old_password = "SecurePass123!"
    new_password = "NewerPass123!"
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"

    _register_user(base_url, username, email, old_password)

    def login(expected_password: str):
        page.goto(f"{base_url}/login", wait_until="domcontentloaded")
        page.fill("#username", username)
        page.fill("#password", expected_password)
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url(f"{base_url}/dashboard")

    def wait_for_toast(message: str):
        page.locator("#toastContainer div", has_text=message).first.wait_for(timeout=2000)

    # Initial login
    login(old_password)

    # Go to profile and change password
    page.goto(f"{base_url}/profile", wait_until="domcontentloaded")
    page.fill("#current_password", old_password)
    page.fill("#new_password", new_password)
    page.fill("#confirm_new_password", new_password)
    page.click("#passwordSubmit")
    wait_for_toast("Password updated successfully")

    # Logout (confirm the dialog)
    page.once("dialog", lambda dialog: dialog.accept())
    page.click("#layoutLogoutBtn")
    page.wait_for_url(f"{base_url}/login")

    # Login with new password
    login(new_password)

    # Ensure dashboard is accessible after re-login
    assert page.url == f"{base_url}/dashboard"


def test_password_change_negative_scenarios(fastapi_server: str, page):
    """
    Negative UI flow: mismatched confirmation and wrong current password should not change the password.
    """
    base_url = fastapi_server.rstrip("/")
    password = "SecurePass123!"
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"

    _register_user(base_url, username, email, password)

    def login(expected_password: str):
        page.goto(f"{base_url}/login", wait_until="domcontentloaded")
        page.fill("#username", username)
        page.fill("#password", expected_password)
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url(f"{base_url}/dashboard")

    def wait_for_toast(message: str):
        page.locator("#toastContainer div", has_text=message).first.wait_for(timeout=2000)

    login(password)
    page.goto(f"{base_url}/profile", wait_until="domcontentloaded")

    # Mismatched confirmation should be blocked client-side
    page.fill("#current_password", password)
    page.fill("#new_password", "Different123!")
    page.fill("#confirm_new_password", "Mismatch456!")
    page.click("#passwordSubmit")
    wait_for_toast("New password and confirmation must match")

    # Wrong current password should be rejected by the API
    page.fill("#current_password", "WrongPass123!")
    page.fill("#new_password", "AnotherPass123!")
    page.fill("#confirm_new_password", "AnotherPass123!")
    page.click("#passwordSubmit")
    wait_for_toast("Current password is incorrect")

    # Logout and verify original password still works (i.e., not changed)
    page.once("dialog", lambda dialog: dialog.accept())
    page.click("#layoutLogoutBtn")
    page.wait_for_url(f"{base_url}/login")

    login(password)
    assert page.url == f"{base_url}/dashboard"
