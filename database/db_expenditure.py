import pandas as pd
from weasyprint import HTML
from io import BytesIO

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

    paid_on = request.paid_on.split("-")
    if len(paid_on) != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enter the date as YYYY-MM-DD.",
        )

    for d in paid_on:
        try:
            int(d)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid dates."
            )

    if 2022 > int(paid_on[0]) > 2023:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid calendar year."
        )
    if 1 > int(paid_on[1]) > 12:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid calendar Month."
        )

    if 1 > int(paid_on[2]) > 31:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid calendar Month."
        )

    paid_on = f"{paid_on[0]}-{paid_on[1]}-{paid_on[2]}"

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

    print(
        f"money_type{new_expenditure.money_type}, amount: "
        f"{new_expenditure.amount}, paid_on {new_expenditure.paid_on}, "
        f"descr{new_expenditure.description}, user_id"
        f"{new_expenditure.user_id}, time_st{new_expenditure.time_stamp}"
    )

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


def expenditures_to_pdf(db: Session, current_user_id: int, response: Response):
    expenditures = (
        db.query(Expenditure).filter(Expenditure.user_id == current_user_id).all()
    )

    user = db.query(User).filter(User.id == current_user_id).first()

    list_of_expenditures = [
        {
            "money type": expenditure.money_type,
            "amount": expenditure.amount,
            "paid on": expenditure.paid_on,
            "description": expenditure.description,
            "time created": expenditure.time_stamp,
        }
        for expenditure in expenditures
    ]

    if not list_of_expenditures:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have no expenses, create on to get " "statement.",
        )

    df = pd.DataFrame(list_of_expenditures)

    # creating readable time_stamps

    for index, time_stamp in enumerate(df["time created"]):
        time_stamp = str(time_stamp)
        day, time = time_stamp.split(" ")[0], time_stamp.split(" ")[1][:8]
        print(f"time stamp: {time_stamp}, day:{day}, time: {time}")
        df.loc[index, "time created"] = f"{day} {time}"

    # create a pdf statement file
    table = df.to_html(classes="my-style", index=False)

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
            text-align: center;
        }}
        
        .summary {{
            text-align: center;   
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
      
      </style>
        <title>HTML Pandas Dataframe with CSS</title>
        <link rel="stylesheet" type="text/css" href="style.css"/>
      </head>
      <body>
      <div class="heading">
        <h3>Transaction statement for {user.first_name} {user.last_name}</h3>
      </div>
        {table}
        <div class="summary">
            <h4>Total credit: <span class="credit"></span> </h4>
            <h4>Total Expenses: <span class="expenses"></span> </h4>
            <h4>Total Amount: <span class="total"></span> </h4>
        </div>
        
      </body>
    </html>
    """
    # TODO: Create the functionality to download the file to users computer
    #  instead of saving it in the server.
    #  The commented code below results to an error about UTF-8 formatting.

    # storing the pdf as BytesIO object
    # pdf_buffer = BytesIO()
    # HTML(string=html_string).write_pdf(pdf_buffer)

    # # Setting the Content-Disposition header
    # # to prompt the user to download the file.
    # response.headers["Content-Disposition"] = f"attachment: filename" \
    #                                           f"={user.username}.pdf"
    #
    # # Setting the Content-Type header to indicate that it's a PDF file
    # response.headers["Content-Type"] = "application/pdf"
    #
    # # Seeking to the beginning of the BytesIO buffer
    # pdf_buffer.seek(0)
    #
    # # Return the PDF as a downloadable file
    # return pdf_buffer.read()

    # # saving the file as pdf.
    HTML(string=html_string).write_pdf(f"{user.username}.pdf")
