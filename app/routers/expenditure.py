from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse

from sqlalchemy.orm.session import Session

from auth.outh2 import get_current_user
from database import db_expenditure
from database.database import get_db
from schema.schemas import (
    ExpenditureBase,
    ExpenditureDisplay,
    UserAuth,
    TransactionBase,
)

router = APIRouter(prefix="/expenditure", tags=["Expenditures"])


@router.post("", response_model=ExpenditureDisplay)
async def create_expenditure(
        request: ExpenditureBase,
        db: Session = Depends(get_db),
        current_user: UserAuth = Depends(get_current_user),
):
    """

    :param request:
    :param db:
    :param current_user:
    :return:
    """
    return db_expenditure.create_expenditure(request, db, current_user.id)


@router.get("", response_model=list[ExpenditureDisplay])
async def user_expenditures(
        db: Session = Depends(get_db), current_user: UserAuth = Depends(get_current_user)
):
    """

    :param db:
    :param current_user:
    :return:
    """
    return db_expenditure.user_expenditures(db, current_user.id)


@router.get('/transactions')
async def transactions(
        db: Session = Depends(get_db), current_user: UserAuth = Depends(get_current_user)):
        
    total_credits, total_expenses, total_transaction, money_at_hand = db_expenditure.total_transactions(db, current_user.id)

    transactions = TransactionBase(
        total_credits=total_credits,
        total_expenses=total_expenses,
        total_transaction=total_transaction,
        money_at_hand=money_at_hand
    )

    return transactions


@router.delete("/delete/{expend_id}")
async def delete_expenditure(
        expend_id: int,
        db: Session = Depends(get_db),
        current_user: UserAuth = Depends(get_current_user),
):
    """

    :param expend_id:
    :param db:
    :param current_user:
    :return:
    """

    return db_expenditure.delete_expenditure(expend_id, db, current_user.id)


@router.put("/edit/{expend_id}")
async def edit_expenditure(
        request: ExpenditureBase,
        expend_id: int,
        db: Session = Depends(get_db),
        current_user: UserAuth = Depends(get_current_user),
):
    """

    :param request:
    :param expend_id:
    :param db:
    :param current_user:
    :return:
    """

    return db_expenditure.edit_expenditure(request, expend_id, db, current_user.id)


@router.get("/statement")
async def get_statement(
        response: Response,
        db: Session = Depends(get_db),
        current_user: UserAuth = Depends(get_current_user),
):
    db_expenditure.expenditures_to_pdf(db, current_user.id, response)
    file_path = f'statements/{current_user.username}.pdf'
    file_name = f'{current_user.username}.pdf'

    return FileResponse(file_path, headers={'Content-disposition': f'attachment; filename={file_name}'})
