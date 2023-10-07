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
        orm_mode = True
        # from_attributes = True


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
        # from_attributes = True
        orm_mode = True


class TransactionBase(BaseModel):
    total_transaction: float
    total_expenses: float
    total_credits: float
    money_at_hand: float



class UserAuth(BaseModel):
    id: int
    username: str
    email: EmailStr
