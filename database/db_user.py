import datetime

from sqlalchemy.orm.session import Session

from fastapi import HTTPException, status

from .hashing import bcrypt, verify

from schema.schemas import UserBase, UserEditUserType, UserEditPassword
from .models import User


def create_user(request: UserBase, db: Session):
    """

    :param request: user request with data
    :param db: the database
    :return: created user dict
    """

    first_name = request.first_name
    last_name = request.last_name

    if len(first_name) < 3 or len(last_name) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Your name must have at least 3 characters.')

    for char in first_name:
        if char.isdigit():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Names must not have digits.')

    for char in last_name:
        if char.isdigit():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Names must not have digits.')

    if len(request.username) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Username must have at least 6 characters.')

    if len(request.password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Password must have at least 6 characters.')

    if request.password.startswith(request.username[0:3]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User password must not start-with username characters.",
        )

    user_types = ['admin', 'user']
    if request.user_type != '':
        if request.user_type.lower() not in user_types:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'User type must be either admin or '
                                       f'user.')

        user_type = request.user_type.lower()
    else:
        user_type = 'user'

    new_user = User(
        first_name=request.first_name.capitalize(),
        last_name=request.last_name.capitalize(),
        username=request.username,
        email=request.email.lower(),
        password=bcrypt(request.password),
        user_image_url=request.user_image_url,
        user_type=user_type,
        created_on=datetime.datetime.now()
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with username '{request.username}' or email '"
                   f"{request.email}' already exists."
        )


def get_all_users(db: Session, current_user_id: int):
    current_user = db.query(User).filter(User.id == current_user_id).first()

    if current_user.user_type == 'admin':
        all_users = db.query(User).all()
        return all_users
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='You are not authorized for this '
                                   'information, contact Admin.')


def delete_user(user_id: int, db: Session, current_user_id: int):
    current_user = db.query(User).filter(User.id == current_user_id).first()
    user = db.query(User).filter(User.id == user_id).first()

    if current_user.user_type == 'admin':
        if user:
            if user.id == current_user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Why the fuck should you delete "
                                           f"yourself. Contact an Admin to "
                                           f"remove you as Admin and ask for "
                                           f"account deletion.")

            if user.user_type == 'admin':
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"You can't delete an Admin.")
            db.delete(user)
            db.commit()
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"User with id '{user_id}' not found.")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='You are not authorized for any deletion, '
                                   'contact Admin.')


def get_user_by_username(username: str, db: Session):
    """Get a user from the database using the username
    Used for authentication.
    Args:
        username (str): user username
        db (Session): the database

    Raises:
        HTTPException: no user found

    Returns:
        dict: user details
        :param username:
        :param db:
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user with username: {username}.')

    return user


def retrieve_user_by_username(username: str, db: Session, current_user_id: int):
    """Get a user from the database using the username
    Used for authentication.
    Args:
        username (str): user username
        db (Session): the database

    Raises:
        HTTPException: no user found

    Returns:
        dict: user details
        :param current_user_id:
        :param username:
        :param db:
    """
    user = db.query(User).filter(User.username == username).first()
    current_user = db.query(User).filter(User.id == current_user_id).first()

    if user:
        if current_user.user_type == 'admin' or current_user.id == user.id:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='You are not authorize to edit other user details.'
            )

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f'No user with username: {username}.')


def edit_user_type(request: UserEditUserType, username: str, db: Session,
                   current_user_id: int):
    user = retrieve_user_by_username(username, db, current_user_id)

    if user:
        user_types = ['admin', 'user']
        if request.user_type != '':
            if request.user_type.lower() not in user_types:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f'User type must be either admin or '
                                           f'user.')

            user_type = request.user_type.lower()
        else:
            user_type = 'user'

        user.user_type = user_type
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Server error'
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'No user with username: {username}'
    )


def edit_user_password(request: UserEditPassword, username: str, db: Session,
                       current_user_id: int):
    user = retrieve_user_by_username(username, db, current_user_id)

    if user:

        if verify(user.password, request.new_password):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='That is the same password you are using.Kindly change '
                       'it.'
            )
        if verify(user.password, request.old_password):
            if len(request.new_password) < 6:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Password must have at least 6 '
                                           'characters.')

            if request.new_password.startswith(user.username[0:3]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User password must not start-with username "
                           f"characters.",
                )

            new_password = bcrypt(request.new_password)
            user.password = new_password
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Old password is not correct, kindly confirm'
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'No user with username {username}'
    )


def reset_password(username: str, db: Session,
                   current_user_id: int):
    user = retrieve_user_by_username(username, db, current_user_id)
    current_user = db.query(User).filter(User.id == current_user_id).first()

    if user:
        if current_user.user_type == 'admin':
            new_password = bcrypt('casher')
            user.password = new_password
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='You are not authorize to edit other user details.'
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'No user with username {username}'
    )
