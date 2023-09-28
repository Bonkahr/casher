from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm.session import Session

from auth.outh2 import get_current_user
from database import db_expenditure
from database.database import get_db
from schema.schemas import ExpenditureBase, ExpenditureDisplay, UserAuth

router = APIRouter(prefix='/expenditure', tags=['Expenditures'])


@router.post('', response_model=ExpenditureDisplay)
async def create_expenditure(request: ExpenditureBase,
                             db: Session = Depends(get_db),
                             current_user: UserAuth = Depends(
                                 get_current_user)):
    """

    :param request:
    :param db:
    :param current_user:
    :return:
    """
    return db_expenditure.create_expenditure(request, db, current_user.id)


@router.get('', response_model=list[ExpenditureDisplay])
async def user_expenditures(db: Session = Depends(get_db),
                            current_user: UserAuth = Depends(
                                get_current_user)):
    """

    :param db:
    :param current_user:
    :return:
    """
    return db_expenditure.user_expenditures(db, current_user.id)


@router.delete('/{expend_id}')
async def delete_expenditure(expend_id: int, db: Session = Depends(get_db),
                             current_user: UserAuth =
                             Depends(get_current_user)):
    """

    :param expend_id:
    :param db:
    :param current_user:
    :return:
    """

    return db_expenditure.delete_expenditure(expend_id, db, current_user.id)


@router.get('/statement')
async def get_statement(response: Response, db: Session = Depends(get_db),
                        current_user: UserAuth = Depends(get_current_user)):
    return db_expenditure.expenditures_to_pdf(db, current_user.id, response)
