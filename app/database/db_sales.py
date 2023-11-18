import datetime
from sqlalchemy.orm.session import Session
from sqlalchemy import text

from fastapi import HTTPException, status

from .models import Sale
from schema.schemas import SaleBase


def correct_sale(request: SaleBase):
    if request.item == "":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Kindly select what you sold."
        )

    if request.bought_amount < 0 or request.sell_amount < 0 or request.balance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sell and bought amount must be greater than zero.",
        )

    if request.sell_amount == 0 and request.mode_of_payment != "gift":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"I have noticed you sold this {request.item} at 0 price, if it was a gift select `gift` on mode of payment.",
        )
    mode_of_payment = ["cash", "mobile money", "gift"]

    if request.mode_of_payment.lower() not in mode_of_payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode of payment may either be `cash`, `mobile money`, `gift`.",
        )

    if request.sell_amount == 0 and request.mode_of_payment != "gift":
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"I have noticed you sold this {request.item} at 0 price, if it was a gift select `gift` on mode of payment.",
        )

    paid_on_date = request.sold_on.split("T")

    print("**********************************\n\n")

    print(paid_on_date)

    
    print("**********************************\n\n")

    paid_on = paid_on_date[0].split("-")

    if len(paid_on) != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enter the date as DD-MM-YYYY.",
        )

    paid_on_dates = [paid_on[0], paid_on[1], paid_on[2][:2]]

    for d in paid_on_dates:
        try:
            int(d)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid dates ->  {paid_on_dates}.",
            )

    if int(paid_on[0]) > 2023 or int(paid_on[0]) < 2022:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid calendar Month."
        )

    if int(paid_on[1]) < 1 or int(paid_on[1]) > 12:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid calendar Month."
        )

    if int(paid_on[2]) > 31 or int(paid_on[2]) < 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid date of the month."
        )

    date_string = f"{paid_on[0]}-{paid_on[1]}-{str(int(paid_on[2]) + 1)}"
    paid_on = datetime.datetime.strptime(date_string, "%Y-%m-%d").date()

    return paid_on


def create_sale(request: SaleBase, db: Session, current_user_id: int):
    paid_on = correct_sale(request)

    entry_amount = request.bought_amount
    sale_amount = request.sell_amount
    balance = request.balance
    profit = sale_amount - (entry_amount + balance)

    new_sale = Sale(
        item=request.item,
        bought_amount=request.bought_amount,
        sell_amount=request.sell_amount,
        mode_of_payment=request.mode_of_payment.lower(),
        transaction_code=request.transaction_code,
        balance=request.balance,
        profit=profit,
        description=request.description,
        sold_on=paid_on,
        user_id=current_user_id,
        created_on=datetime.datetime.now(),
    )

    try:
        db.add(new_sale)
        db.commit()
        db.refresh(new_sale)
        return new_sale

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error saving your data, try again later.",
        )


def user_sales(db: Session, current_user_id: int):
    sales = (
        db.query(Sale)
        .filter(Sale.user_id == current_user_id)
        .order_by(Sale.sold_on.desc())
        .all()
    )

    return sales


def daily_sales(date: str, db: Session, current_user_id: int):
    sales = (
        db.query(Sale)
        .filter(Sale.user_id == current_user_id)
        .filter(Sale.sold_on == date)
        .order_by(Sale.sold_on.desc())
        .all()
    )
    return sales


def generic_transaction_func(sales):
    buy_price = []
    all_sales = []
    all_profit = []
    on_debpt = []

    for sale in sales:
        buy_price.append(sale.bought_amount)
        all_sales.append(sale.sell_amount)
        all_profit.append(sale.profit)
        on_debpt.append(sale.balance)

    total_buy_price = sum(buy_price)
    total_daily_sales = sum(all_sales)
    total_daily_profit = sum(all_profit)
    total_debpt = sum(on_debpt)

    try:
        percentage_profit = (total_daily_profit / total_buy_price) * 100
        return (total_daily_sales, total_daily_profit, total_debpt, percentage_profit)
    except Exception as e:
        return 0, 0, 0, 0


def daily_transaction(date: str, db: Session, current_user_id: int):
    sales = (
        db.query(Sale)
        .filter(Sale.user_id == current_user_id)
        .filter(Sale.sold_on == date)
        .all()
    )

    if sales:
        return generic_transaction_func(sales)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"You have no transactions on date {date}.",
    )


def generic_duration_func(
    db: Session, current_user_id: int, start_date: int, end_date: int
):
    text_query = text(
        "SELECT * FROM sale WHERE user_id = :id AND sold_on >= :start_date AND sold_on <= :end_date"
    )
    sales = db.execute(
        text_query,
        {
            "start_date": f"{start_date}",
            "end_date": f"{end_date}",
            "id": f"{current_user_id}",
        },
    )

    return sales


def transaction_history(db: Session, current_user_id: int):
    today = datetime.datetime.today()

    date = f"{today.year}-{today.month}-{today.day}"
    today_sale = generic_duration_func(db, current_user_id, date, date)
    today_sales = generic_transaction_func(today_sale)

    week_day = today.strftime("%w")
    week_start = f"{today.year}-{today.month}-{today.day - int(week_day)}"
    week_end = f"{today.year}-{today.month}-{today.day}"
    weekly_sale = generic_duration_func(db, current_user_id, week_start, week_end)
    week_sales = generic_transaction_func(weekly_sale)

    start_date = f"{today.year}-{today.month}-1"
    end_date = f"{today.year}-{today.month}-31"
    monthly_sales = generic_duration_func(db, current_user_id, start_date, end_date)
    monthly = generic_transaction_func(monthly_sales)

    all_sales = db.query(Sale).filter(Sale.user_id == current_user_id).all()
    all_sale = generic_transaction_func(all_sales)

    return today_sales, week_sales, monthly, all_sale


def filter_by_balance(db: Session, current_user_id: int):
    sales = (
        db.query(Sale)
        .filter(Sale.user_id == current_user_id)
        .filter(Sale.balance > 0)
        .all()
    )
    return sales


def delete_sale(sale_id: int, db: Session, current_user_id: int):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()

    if sale:
        if sale.user_id == current_user_id:
            db.delete(sale)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can only delete your own sales.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"No sale with id {sale_id}."
        )
