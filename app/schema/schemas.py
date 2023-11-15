from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    user_type: str


class UserEditPassword(BaseModel):
    old_password: str
    new_password: str


class UserEditUserType(BaseModel):
    user_type: str


class UserDisplay(BaseModel):
    id: int
    first_name: str
    last_name: str
    user_type: str
    username: str
    user_image_url: str
    created_on: datetime

    class Config:
        # orm_mode = True
        from_attributes = True


class ExpenditureBase(BaseModel):
    money_type: str
    amount: float
    paid_on: str
    description: str


class ExpenditureDisplay(BaseModel):
    money_type: str
    amount: float
    paid_on: str
    description: str
    id: int
    time_stamp: datetime

    class Config:
        from_attributes = True
        # orm_mode = True


class TransactionBase(BaseModel):
    total_transaction: float
    total_expenses: float
    total_credits: float
    money_at_hand: float


class UserAuth(BaseModel):
    id: int
    username: str
    email: EmailStr


class SaleBase(BaseModel):
    item: str
    bought_amount: int
    sell_amount: int
    mode_of_payment: str
    transaction_code: str
    balance: int
    description: str
    sold_on: str


class SaleDisplay(BaseModel):
    id: int
    item: str
    bought_amount: int
    sell_amount: int
    mode_of_payment: str
    transaction_code: str
    balance: int
    profit: int
    description: str
    sold_on: str
    user_id: int
    created_on: datetime
    user: UserAuth

    class Config:
        from_attributes = True


class SalesTransactionDisplay(BaseModel):
    total_sales: int
    total_profits: int
    total_debpts: int
    percentage_profit: float


class TransactionHistoryDisplay(BaseModel):
    today_sales: int
    today_profits: int
    today_debpts: int
    today_perc_profit: float
    weekly_sales: int
    weekly_profits: int
    weekly_debpts: int
    weekly_perc_profit: float
    monthly_sales: int
    monthly_profits: int
    monthly_debpts: int
    monthly_perc_profit: float
    all_sales: int
    all_profits: int
    all_debpts: int
    all_perc_profit: float
