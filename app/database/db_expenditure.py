import os

import pandas as pd
from weasyprint import HTML

import datetime

from sqlalchemy.orm.session import Session

from fastapi import HTTPException, status, Response

from schema.schemas import ExpenditureBase
from .models import Expenditure, User


def correct_expenditure(request: ExpenditureBase):
    money_type = ["credit", "expense"]

    if request.money_type.lower() not in money_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Type must either be credit or expense.",
        )
    money_type = request.money_type.lower()

    if request.amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Was {request.amount} a loan? Record it as credit with a description of loan.'
        )

    paid_on_separator = set([x for x in request.paid_on if not x.isalnum()])

    if len(paid_on_separator) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid dates."
        )

    paid_on = request.paid_on.split(list(paid_on_separator)[0])

    if len(paid_on) != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enter the date as DD-MM-YYYY.",
        )

    for d in paid_on:
        try:
            int(d)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid dates."
            )

    if int(paid_on[0]) > 31 or int(paid_on[0]) < 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid date of the month."
        )

    if int(paid_on[1]) < 1 or int(paid_on[1]) > 12:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Month of transaction."
        )

    if int(paid_on[2]) > 2023 or int(paid_on[2]) < 2022:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Year."
        )

    paid_on = f"{paid_on[2]}-{paid_on[1]}-{paid_on[0]}"

    return money_type, paid_on


def create_expenditure(request: ExpenditureBase, db: Session, current_user_id: int):
    money_type, paid_on = correct_expenditure(request)

    new_expenditure = Expenditure(
        money_type=money_type,
        amount=request.amount,
        paid_on=paid_on,
        description=request.description,
        user_id=current_user_id,
        time_stamp=datetime.datetime.now(),
    )

    # print(
    #     f"money_type{new_expenditure.money_type}, amount: "
    #     f"{new_expenditure.amount}, paid_on {new_expenditure.paid_on}, "
    #     f"descr{new_expenditure.description}, user_id"
    #     f"{new_expenditure.user_id}, time_st{new_expenditure.time_stamp}"
    # )

    try:
        db.add(new_expenditure)
        db.commit()
        db.refresh(new_expenditure)
        return new_expenditure
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error saving your data to the database. Try again later.",
        )


def user_expenditures(db: Session, current_user_id: int):
    expenditures = (
        db.query(Expenditure)
        .filter(Expenditure.user_id == current_user_id)
        .order_by(Expenditure.time_stamp.desc())
        .all()
    )

    return expenditures


def delete_expenditure(expend_id: int, db: Session, current_user_id: int):
    expenditure = db.query(Expenditure).filter(Expenditure.id == expend_id).first()
    if expenditure:
        if expenditure.user_id == current_user_id:
            db.delete(expenditure)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can only delete your expenditures.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No expenditure with id {expend_id}.",
        )


def edit_expenditure(
    request: ExpenditureBase, expend_id: int, db: Session, current_user_id: int
):
    expenditure = db.query(Expenditure).filter(Expenditure.id == expend_id).first()

    if not expenditure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No expenditure with id {expend_id}.",
        )

    if not expenditure.user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"You are not authorized to edit this " f"expenditure.",
        )

    money_type, paid_on = correct_expenditure(request)

    expenditure.money_type = money_type
    expenditure.paid_on = paid_on
    expenditure.amount = request.amount
    expenditure.description = request.description
    expenditure.time_stamp = datetime.datetime.now()

    try:
        db.add(expenditure)
        db.commit()
        db.refresh(expenditure)
        return expenditure
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error saving your data to the database. Try again later.",
        )


def total_transactions(db: Session, current_user_id: int):
    expenditures = (
        db.query(Expenditure).filter(Expenditure.user_id == current_user_id).all()
    )

    credits = []
    expenses = []

    for expend in expenditures:
        if expend.money_type == "credit":
            credits.append(expend.amount)
        else:
            expenses.append(expend.amount)

    total_credits = sum(credits)
    total_expenses = sum(expenses)
    total_transaction = sum(credits) + sum(expenses)
    money_at_hand = sum(credits) - sum(expenses)

    return (total_credits, total_expenses, total_transaction, money_at_hand)


def expenditures_to_pdf(db: Session, current_user_id: int, response: Response):
    expenditures = (
        db.query(Expenditure)
        .filter(Expenditure.user_id == current_user_id)
        .order_by(Expenditure.time_stamp.desc())
        .all()
    )

    user = db.query(User).filter(User.id == current_user_id).first()

    list_of_expenditures = [
        {
            "Money Type": expenditure.money_type,
            "Amount": expenditure.amount,
            "Paid On": expenditure.paid_on,
            "Description": expenditure.description,
            "Time Created": expenditure.time_stamp,
        }
        for expenditure in expenditures
    ]

    if not list_of_expenditures:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have no expenses, create an expenditure to get statement.",
        )

    df = pd.DataFrame(list_of_expenditures)

    # creating readable time_stamps

    for index, time_stamp in enumerate(df["Time Created"]):
        time_stamp = str(time_stamp)
        day, time = time_stamp.split(" ")[0], time_stamp.split(" ")[1][:8]
        df.loc[index, "Time Created"] = f"{day} {time}"

    # create a pdf statement file
    table = df.to_html(classes="my-style", index=False)

    (
        total_credits,
        total_expenses,
        total_transaction,
        money_at_hand,
    ) = total_transactions(db, current_user_id)

    html_string = f"""
    <html>
      <head>
      
      <style>
        .my-style {{
            font-size: 11px;
            font-family: Arial;
            border-collapse: collapse;
            border: 3px solid silver;
        
            }}
        
        .my-style td, th {{
            padding: 10px;
            text-align: right;
            margin-right: 3px;
        }}
        
        .my-style tr:nth-child(even) {{
            background: #E0E0E0;
        }}
        
        .my-style tr:hover {{
            background: silver;
            cursor: pointer;
        }}
        
        .heading {{
            color: green;
            margin-bottom: 4px;
            text-align: left;
        }}

        .table {{
            margin: auto;
            text-align: center; 
        }}
        
        .summary {{
            text-align: left;   
        }}
        
        .credit {{
            color: #0E8787;
        }}
        
        .expenses {{
            color: #E42F17;
        }}
        
        .total {{
            color: #55E329;
        }}

        .athand {{
            color: #E419B7;
        }}

      </style>
        <title>{user.username} Casher app expenditure statement</title>
        <link rel="stylesheet" type="text/css" href="style.css"/>
      </head>
      <body>
      <div class="heading">
        <h3><em>Transaction statement for {user.first_name} {user.last_name}</em></h3>
      </div>
      <div class="table">
        {table}
      </div>
      <div class="summary">
        <h6>Total credit      : <span class="credit">{format(total_credits, '.2f')}</span></h6>
        <h6>Total Expenses    : <span class="expenses">{format(total_expenses, '.2f')}</span></h6>
        <h6>Total Transactions: <span class="total">{format(total_transaction, '.2f')}</span></h6>
        <h6>Money at hand     : <span class="athand">{format(money_at_hand, '.2f')}</span></h6>
      </div>        
      </body>
    </html>
    """
    statement_files = os.listdir("statements")

    for file in statement_files:
        if file == f"{user.username}.pdf":
            os.remove(f"statements/{file}")

    HTML(string=html_string).write_pdf(f"statements/{user.username}.pdf")
