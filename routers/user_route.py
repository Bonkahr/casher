from fastapi import APIRouter, Depends
from sqlalchemy.orm.session import Session

from auth.outh2 import get_current_user
from database import db_user
from database.database import get_db
from schema.schemas import UserBase, UserDisplay, UserAuth

router = APIRouter(prefix='/user', tags=['Users'])


@router.post('', response_model=UserDisplay)
async def create_user(request: UserBase, db: Session = Depends(get_db)):
    """

    :param request: user data
    :param db: the database
    :return: the created user
    """

    return db_user.create_user(request, db)


@router.get('', response_model=list[UserDisplay])
async def all_users(db: Session = Depends(get_db),
                    current_user: UserAuth = Depends(get_current_user)):
    """

    :param current_user:
    :param db: the database
    :return: all users
    """
    return db_user.get_all_users(db, current_user.id)


@router.delete('/{user_id}')
async def delete_user(user_id: int, db: Session = Depends(get_db),
                      current_user: UserAuth = Depends(get_current_user)):
    """

    :param current_user:
    :param user_id:
    :param db:
    :return:
    """
    return db_user.delete_user(user_id, db, current_user.id)
