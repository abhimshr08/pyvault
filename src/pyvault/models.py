from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    totp_secret = Column(String, nullable=True)

    passwords = relationship("Password", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(email='{self.email}')>"

class Password(Base):
    __tablename__ = 'passwords'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    service = Column(String, nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(String, nullable=False)

    user = relationship("User", back_populates="passwords")

    __table_args__ = (
        UniqueConstraint('user_id', 'service', name='_user_service_uc'),
    )

    def __repr__(self):
        return f"<Password(service='{self.service}', username='{self.username}')>"