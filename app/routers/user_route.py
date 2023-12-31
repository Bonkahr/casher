import shutil
import os

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm.session import Session

from auth.outh2 import get_current_user
from database import db_user
from database.database import get_db
from database.models import User
from schema.schemas import (
    UserBase,
    UserDisplay,
    UserAuth,
    UserEditUserType,
    UserEditPassword,
)

router = APIRouter(prefix="/user", tags=["Users"])


@router.post("/new", response_model=UserDisplay)
async def create_user(request: UserBase, db: Session = Depends(get_db)):
    """

    :param request: user data
    :param db: the database
    :return: the created user
    """

    return db_user.create_user(request, db)


@router.get("", response_model=list[UserDisplay])
async def all_users(
    db: Session = Depends(get_db), current_user: UserAuth = Depends(get_current_user)
):
    """

    :param current_user:
    :param db: the database
    :return: all users
    """
    return db_user.get_all_users(db, current_user.id)


@router.get("/{username}", response_model=UserDisplay)
async def get_user_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_user.retrieve_user_by_username(username, db, current_user.id)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    """

    :param current_user:
    :param user_id:
    :param db:
    :return:
    """
    return db_user.delete_user(user_id, db, current_user.id)


@router.put("/edit_user/{username}", response_model=UserDisplay)
async def edit_user_type(
    request: UserEditUserType,
    username: str,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_user.edit_user_type(request, username, db, current_user.id)


@router.put("/edit_password/{username}", response_model=UserDisplay)
async def change_password(
    request: UserEditPassword,
    username: str,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_user.edit_user_password(request, username, db, current_user.id)


@router.put("/reset_password/{username}", response_model=UserDisplay)
async def reset_password(
    username: str,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_user.reset_password(username, db, current_user.id)


@router.post("/image")
async def upload_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    """Uploads an image to the server

    Args:
        image (UploadFile, optional): the image file.
        Default to File(...).
        Current_user (UserAuth, optional): logged user.
        Defaults Depend on(get_current_user).

    Raises:
        HTTPException: image file not supported

    Returns:
        str: file name saved in server
        :param image:
        :param current_user:
    """

    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must log in to upload an image.",
        )

    image_file_type = image.filename.rsplit(".", 1)[1]

    allowed_image_types = {"jpg", "png", "jpeg", "webm", "gif", "svg"}

    if image_file_type not in allowed_image_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image format not supported, supported "
            f'formats are {", ".join(allowed_image_types)}.',
        )

    filename = image.filename.rsplit(".", 1)

    images = os.listdir(path='images')

    for pic in images:
        pic_name = pic.rsplit(".", 1)[0]
        if pic_name == user.username:
            os.remove(f'images/{pic}')
    
    path = f"images/{user.username}.{filename[-1]}"

    with open(path, "w+b") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    try:
        user.user_image_url = f'{path}'
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Error in Server, try again later.')

    return {"file_name": path}
