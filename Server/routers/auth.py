from fastapi import HTTPException, status, APIRouter, Depends
from pydantic import BaseModel

from Server.utils import utils

router = APIRouter(prefix="/auth")


class UserRequest(BaseModel):
    username: str
    password: str


@router.post("/register", status_code=status.HTTP_204_NO_CONTENT)
async def register(request: UserRequest, users_table=Depends(utils.get_user_manager)):
    """check if a username is registered, if it is then raise an exception. if not, register it."""
    pw_error_messages = await utils.validate_strong_password(request.password)
    if pw_error_messages:  # if not None = password is bad
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="\n".join(pw_error_messages))

    # try to save the user in the database
    if not users_table.save_user(request.username, request.password):  # register and check if username taken
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User already exists.")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


@router.post("/login")
def login(request: UserRequest, users_table=Depends(utils.get_user_manager)) -> LoginResponse:
    """check if a username is registered with the correct password, if it is then log in,
    if not then raise an exception."""
    if not users_table.verify_pair(request.username, request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Username or password is wrong.")

    user = users_table.get_user_by_username(request.username)
    access_token = utils.create_access_token(user.id, user.username)  # grant access token
    refresh_token = utils.create_refresh_token(user.id, user.username)  # grant refresh token

    return LoginResponse(access_token=access_token,
                         refresh_token=refresh_token)


@router.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_data: dict = Depends(utils.get_user_data), users_table=Depends(utils.get_user_manager)):
    """delete user from the database"""
    users_table.delete_user(user_data["user_id"])


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/refresh_token")
def refresh(user_data: dict = Depends(utils.get_refresh_token_data)) -> RefreshResponse:
    """remove the old access token and issue a new access token to the client so they don't get logged out"""
    new_token = utils.create_access_token(user_data["user_id"], user_data["username"])

    return RefreshResponse(access_token=new_token)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change_password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(request: ChangePasswordRequest, user_data: dict = Depends(utils.get_user_data),
                          users_table=Depends(utils.get_user_manager)):
    """change the users password to the new password, provided the old password is correct"""

    if not users_table.verify_pair(user_data["username"], request.old_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Old password incorrect.")

    # check if new password is strong enough
    pw_error_messages = await utils.validate_strong_password(request.new_password)
    if pw_error_messages:  # if not None = password is bad
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="\n".join(pw_error_messages))

    # good
    users_table.update_password(user_data["user_id"], request.new_password)
