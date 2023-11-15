from fastapi import APIRouter, Depends

from sqlalchemy.orm.session import Session
from auth.outh2 import get_current_user
from database import db_sales
from database.database import get_db
from schema.schemas import (
    SaleBase,
    UserAuth,
    SaleDisplay,
    SalesTransactionDisplay,
    TransactionHistoryDisplay,
)


router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post("", response_model=SaleDisplay)
async def create_sale(
    request: SaleBase,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_sales.create_sale(request, db, current_user.id)


@router.get("/all-sales", response_model=list[SaleDisplay])
async def get_all_sales(
    db: Session = Depends(get_db), current_user: UserAuth = Depends(get_current_user)
):
    return db_sales.user_sales(db, current_user.id)


@router.get("/on-date/{date}", response_model=list[SaleDisplay])
async def get_sales_by_date(
    date,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_sales.daily_sales(date, db, current_user.id)


@router.get("/trasactions/{date}")
async def sales_transactions(
    date,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    sales, debpts, profit, percentage_profit = db_sales.daily_transaction(
        date, db, current_user.id
    )

    transactions = SalesTransactionDisplay(
        total_sales=sales,
        total_profits=profit,
        total_debpts=debpts,
        percentage_profit=format(percentage_profit, ".2f"),
    )
    return transactions


@router.get("/transaction-hisory")
async def transaction_history(
    db: Session = Depends(get_db), current_user: UserAuth = Depends(get_current_user)
):
    today, weekly, monthly, all_sales = db_sales.transaction_history(db, current_user.id)

    today_sales, today_profits, today_debpts, today_perc_profit = today
    weekly_sales, weekly_profits, weekly_debts, weekly_perc_profit = weekly
    monthly_sales, monthly_profits, monthly_debts, monthly_perc_profit = monthly
    all_sales, all_profits, all_debpts, all_perc_profit = all_sales

    transactions = TransactionHistoryDisplay(
        today_sales=today_sales,
        today_profits=today_profits,
        today_debpts=today_debpts,
        today_perc_profit=format(today_perc_profit, '.2f'),
        weekly_sales=weekly_sales,
        weekly_profits=weekly_profits,
        weekly_debpts=weekly_debts,
        weekly_perc_profit=format(weekly_perc_profit, '.2f'),
        monthly_sales=monthly_sales,
        monthly_profits=monthly_profits,
        monthly_debpts=monthly_debts,
        monthly_perc_profit=format(monthly_perc_profit, '.2f'),
        all_sales=all_sales,
        all_debpts=all_debpts,
        all_profits=all_profits,
        all_perc_profit=format(all_perc_profit, '.2f')
    )

    return transactions


@router.get("/depts", response_model=list[SaleDisplay])
async def sales_on_debpt(
    db: Session = Depends(get_db), current_user: UserAuth = Depends(get_current_user)
):
    return db_sales.filter_by_balance(db, current_user.id)


@router.delete("/{sale_id}")
async def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: UserAuth = Depends(get_current_user),
):
    return db_sales.delete_sale(sale_id, db, current_user.id)
