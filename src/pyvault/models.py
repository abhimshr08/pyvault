from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Password(Base):
    __tablename__ = 'passwords'

    id = Column(Integer, primary_key=True)
    service = Column(String, nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)

    def __repr__(self):
        return f"<Password(service='{self.service}', username='{self.username}')>"