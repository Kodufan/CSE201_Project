from sqlalchemy import Column, Float, String, Integer, Enum, DateTime, ForeignKey, Boolean
from database import Base
from schemas import accessLevel


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

    commentID = Column(Integer, primary_key=True, autoincrement=True)
    placeID = Column(Integer, ForeignKey("places.placeID"))
    rating = Column(Integer, nullable=False)
    username = Column(String(20), ForeignKey("users.username"))
    commentBody = Column(String(2000))

class Thumbnail(Base):
    __tablename__ = "images"

    imageID = Column(Integer, primary_key=True, autoincrement=True)
    imageURL = Column(String(200), nullable=False)
    placeID = Column(Integer, ForeignKey("places.placeID"))
