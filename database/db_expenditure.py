import datetime

from sqlalchemy.orm.session import Session

from fastapi import HTTPException, status

from schema.schemas import ExpenditureBase
from .models import Expenditure


def create_expenditure(request: ExpenditureBase, db: Session,
                       current_user_id: int):

    money_type = ['credit', 'expense']

    if request.money_type not in money_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Type must either be credit or expense.'
        )
    money_type = request.money_type.lower()

    paid_on = request.paid_on.split('-')
    if len(paid_on) != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Enter the date as YYYY-MM-DD.'
        )

    for d in paid_on:
        try:
            int(d)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Invalid dates.'
            )

    if 2022 > int(paid_on[0]) > 2023:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Invalid calendar year.'
        )
    if 1 > int(paid_on[1]) > 12:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Invalid calendar Month.'
        )

    if 1 > int(paid_on[2]) > 31:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f'Invalid calendar Month.'
        )

    paid_on = f'{paid_on[0]}-{paid_on[1]}-{paid_on[2]}'

    new_expenditure = Expenditure(
        money_type=money_type,
        amount=request.amount,
        paid_on=paid_on,
        description=request.description,
        user_id=current_user_id,
        time_stamp=datetime.datetime.now()
    )

    print(f"money_type{new_expenditure.money_type}, amount: "
          f"{new_expenditure.amount}, paid_on {new_expenditure.paid_on}, "
          f"descr{new_expenditure.description}, user_id"
          f"{new_expenditure.user_id}, time_st{new_expenditure.time_stamp}")

    try:
        db.add(new_expenditure)
        db.commit()
        db.refresh(new_expenditure)
        return new_expenditure
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error saving your data to the database. Try again later."
        )


def get_all_expenditures(db: Session, current_user_id):
    expenditures = db.query(Expenditure).\
        filter(Expenditure.user_id == current_user_id).all()
    return expenditures
