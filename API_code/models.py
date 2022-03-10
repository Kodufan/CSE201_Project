from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Integer, String)

from config import TOKEN_LENGTH
from database import Base
from schemas import accessLevel, tokenType


class User(Base):
    __tablename__ = "users"

    username = Column(String(20), unique=True)
    email = Column(String(100), primary_key=True)
    verified = Column(Boolean, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    accessLevel = Column(Enum(accessLevel), nullable=False)
    accountCreated = Column(DateTime)

class Place(Base):
    __tablename__ = "places"

    placeID = Column(Integer, primary_key=True, autoincrement=True)
    posterID = Column(String(20), ForeignKey("users.username", ondelete="CASCADE", onupdate="CASCADE"))
    plusCode = Column(String(100), nullable=False)
    friendlyName = Column(String(100), nullable=False)
    country = Column(String(6))
    description = Column(String(1000))
    rating = Column(Float)
    isvisible = Column(Boolean, nullable=False)

class Comment(Base):
    __tablename__ = "comments"

    ratingID = Column(Integer, primary_key=True, autoincrement=True)
    placeID = Column(Integer, ForeignKey("places.placeID", ondelete="CASCADE"))
    ratingValue = Column(Integer, nullable=False)
    username = Column(String(20), ForeignKey("users.username", ondelete="CASCADE", onupdate="CASCADE"))
    commentBody = Column(String(2000))
    timePosted = Column(DateTime, nullable=False)
    timeEdited = Column(DateTime, nullable=False)

class Thumbnail(Base):
    __tablename__ = "images"

    imageID = Column(Integer, primary_key=True, autoincrement=True)
    uploader = Column(String(20), nullable=False)
    verified = Column(Boolean, nullable=False)
    placeID = Column(Integer, ForeignKey("places.placeID", ondelete="CASCADE"))
    externalURL = Column(String(200), nullable=False)
    internalURL = Column(String(200), nullable=False)
    uploadDate = Column(DateTime, nullable=False)


class Token(Base):
    __tablename__ = "tokens"

    email = Column(String(100), ForeignKey("users.email", ondelete="CASCADE"), primary_key=True)
    type = Column(Enum(tokenType), nullable=False, primary_key=True)
    token = Column(String(TOKEN_LENGTH), nullable=False, unique=True)
    expires = Column(DateTime, nullable=False)
