from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Float
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    user_image_url = Column(String)
    user_type = Column(String)
    created_on = Column(DateTime)
    expenditures = relationship('Expenditure', back_populates='user', cascade='all, delete, delete-orphan')


class Expenditure(Base):
    __tablename__ = 'expenditure'

    id = Column(Integer, primary_key=True, index=True)
    money_type = Column(String)
    amount = Column(Float)
    paid_on = Column(String)
    description = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', back_populates='expenditures')
    time_stamp = Column(DateTime)
