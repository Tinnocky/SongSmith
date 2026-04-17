from http import HTTPStatus as Status

from client_utils import run_request


def register() -> tuple[str, str, str]:
    """input username and password, run register request and return a tuple containing the
    username and the token to save."""
    while True:
        username = input("Enter Username: ")
        password = input("Enter Password: ")

        response = run_request(
            "POST",
            "/auth/register",
            json={"username": username, "password": password}
        )

        if response.status_code == Status.NO_CONTENT:  # got an okay
            return login(username, password)  # login + return the username and token tuple from it

        elif response.status_code == Status.CONFLICT:
            print("Username already taken.")

        elif response.status_code == Status.BAD_REQUEST:
            print(response.json()["detail"])

        # didn't go through, try again next iteration


def login(username: str = None, password: str = None) -> tuple[str, str, str]:
    """input username and password, run login request and return a tuple containing the
    username and the token to save."""
    while True:
        if not username:
            username = input("Enter Username: ")
        if not password:
            password = input("Enter Password: ")

        response = run_request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password}
        )

        if response.status_code == Status.OK:
            return username, response.json()["access_token"], response.json()["refresh_token"]

        # didn't go through, try again next iteration
        username, password = None, None  # reset


def change_password() -> bool | None:
    """input old and new passwords and run change password request"""

    while True:
        old_password = input("Enter old password (or BACK to stop): ")
        if old_password.upper() == "BACK":
            return None  # go back

        new_password = input("Enter new password (or BACK to stop): ")
        if new_password.upper() == "BACK":
            return None  # go back

        response = run_request(
            "POST",
            "/auth/change_password",
            json={
                "old_password": old_password,
                "new_password": new_password
            }
        )

        if response.status_code == Status.NO_CONTENT:  # ok
            return True

        if response.status_code == Status.UNAUTHORIZED:  # error
            print(response.json()["detail"])

        # didn't go through, try again next iteration


def delete_account() -> bool:
    """runs the /auth/delete request, and delete"""
    confirmation = input("Are you sure? This cannot be undone. (YES to confirm): ")
    if confirmation.strip().upper() != "YES":
        print("Cancelled.")
        return False

    response = run_request("DELETE", "/auth/user")

    return response.status_code == Status.NO_CONTENT
