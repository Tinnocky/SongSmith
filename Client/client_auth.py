from http import HTTPStatus as Status

from Client.client_utils import run_request


def register(username: str, password: str) -> dict[str, str] | str:
    response = run_request(
        "POST",
        "/auth/register",
        json={"username": username, "password": password}
    )

    if response.status_code == Status.NO_CONTENT:  # got an okay
        return login(username, password)  # login + return the username and token tuple from it

    # didn't go through
    elif response.status_code == Status.BAD_REQUEST:
        return response.json().get("detail", "Something went wrong.")

    return "Username already taken."  # Status.CONFLICT


def login(username: str, password: str) -> dict[str, str] | str:
    response = run_request(
        "POST",
        "/auth/login",
        json={"username": username, "password": password}
    )

    if response.status_code == Status.OK:
        return {
            "username": username,
            "access_token": response.json()["access_token"],
            "refresh_token": response.json()["refresh_token"]
        }

    # didn't go through
    return response.json().get("detail", "Something went wrong.")  # "Username or password is wrong."


def change_password(old_password: str, new_password: str) -> str | None:
    response = run_request(
        "POST",
        "/auth/change_password",
        json={
            "old_password": old_password,
            "new_password": new_password
        }
    )

    if response.status_code == Status.NO_CONTENT:  # ok
        return None # success

    return response.json().get("detail", "Something went wrong.")  # didn't go through


def delete_account() -> bool:
    response = run_request("DELETE", "/auth/user")
    return response.status_code == Status.NO_CONTENT
