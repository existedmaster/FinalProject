from uuid import uuid4

import requests


def test_login_profile_password_change_and_relogin(fastapi_server: str, page):
    """
    Full UI flow:
    1) Create a user via API.
    2) Login via the web UI.
    3) Change password on the profile page.
    4) Logout and login again with the new password.
    """
    base_url = fastapi_server.rstrip("/")
    old_password = "SecurePass123!"
    new_password = "NewerPass123!"
    username = f"user_{uuid4().hex[:8]}"
    email = f"{username}@example.com"

    # Create user via API
    reg_resp = requests.post(
        f"{base_url}/auth/register",
        json={
            "first_name": "Flow",
            "last_name": "Tester",
            "email": email,
            "username": username,
            "password": old_password,
            "confirm_password": old_password,
        },
        timeout=10,
    )
    assert reg_resp.status_code == 201, reg_resp.text

    def login(expected_password: str):
        page.goto(f"{base_url}/login", wait_until="domcontentloaded")
        page.fill("#username", username)
        page.fill("#password", expected_password)
        page.get_by_role("button", name="Sign in").click()
        page.wait_for_url(f"{base_url}/dashboard")

    # Initial login
    login(old_password)

    # Go to profile and change password
    page.goto(f"{base_url}/profile", wait_until="domcontentloaded")
    page.fill("#current_password", old_password)
    page.fill("#new_password", new_password)
    page.fill("#confirm_new_password", new_password)
    page.click("#passwordSubmit")
    page.wait_for_timeout(500)  # allow toast script to run

    # Logout (confirm the dialog)
    page.once("dialog", lambda dialog: dialog.accept())
    page.click("#layoutLogoutBtn")
    page.wait_for_url(f"{base_url}/login")

    # Login with new password
    login(new_password)

    # Ensure dashboard is accessible after re-login
    assert page.url == f"{base_url}/dashboard"
