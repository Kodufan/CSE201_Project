from sqlalchemy import (Boolean, Column, DateTime, Enum, Float, ForeignKey,
                        Integer, String)

from database import Base
from schemas import accessLevel, tokenType
from config import TOKEN_LENGTH


class User(Base):
    __tablename__ = "users"

    username = Column(String(20), primary_key=True)
    hashed_password = Column(String(100), nullable=False)
    accessLevel = Column(Enum(accessLevel), nullable=False)
    accountCreated = Column(DateTime)

    #items = relationship("Item", back_populates="owner")

class Place(Base):
    __tablename__ = "places"

    placeID = Column(Integer, primary_key=True, autoincrement=True)
    posterID = Column(String(20), ForeignKey("users.username"))
    plusCode = Column(String(100), nullable=False)
    friendlyName = Column(String(100), nullable=False)
    country = Column(String(6))
    description = Column(String(1000))
    rating = Column(Float)
    isvisible = Column(Boolean, nullable=False)

    #owner = relationship("User", back_populates="items")

class Comment(Base):
    __tablename__ = "comments"

    ratingID = Column(Integer, primary_key=True, autoincrement=True)
    placeID = Column(Integer, ForeignKey("places.placeID"))
    ratingValue = Column(Integer, nullable=False)
    username = Column(String(20), ForeignKey("users.username"))
    commentBody = Column(String(2000))
    timePosted = Column(DateTime, nullable=False)
    timeEdited = Column(DateTime)

class Thumbnail(Base):
    __tablename__ = "images"

    imageID = Column(Integer, primary_key=True, autoincrement=True)
    uploader = Column(String(20), nullable=False)
    placeID = Column(Integer, ForeignKey("places.placeID"))
    externalURL = Column(String(200), nullable=False)
    internalURL = Column(String(200), nullable=False)
    uploadDate = Column(DateTime, nullable=False)

class Token(Base):
    __tablename__ = "tokens"

    username = Column(String(20), ForeignKey("users.username"), primary_key=True)
    type = Column(Enum(tokenType), nullable=False, primary_key=True)
    token = Column(String(TOKEN_LENGTH), nullable=False, unique=True)
    expires = Column(DateTime, nullable=False)