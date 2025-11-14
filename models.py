from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint, Index, DateTime, func

Base =  declarative_base()

class UserModel(Base):
    __tablename__ = "users-3"
    id = Column(Integer,primary_key=True)
    name = Column(String(32), index=True, nullable=False)
    email = Column(String(64),unique=True, nullable=False)
    create_at = Column(DateTime(timezone=True), server_default=func.now(),nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
