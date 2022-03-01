from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey, null
from geoalchemy2 import Geometry
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
    location = Column(Geometry('POINT'), nullable=False)
    title = Column(String(60), nullable=False)
    description = Column(String(1000))
    

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
