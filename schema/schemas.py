from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    user_image_url: str
    user_type: str
    created_on: datetime


class UserDisplay(BaseModel):
    first_name: str
    last_name: str
    user_type: str
    created_on: datetime

    class Config:
        # orm_mode = True
        from_attributes = True


class ExpenditureBase(BaseModel):
    money_type: str
    amount: float
    paid_on: str
    description: str
    time_stamp: datetime


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


class UserAuth(BaseModel):
    id: int
    username: str
    email: EmailStr

