from typing import List
from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey, null
from geoalchemy2 import Geometry
from yarl import URL
from database import Base
from schemas import accessLevel


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    accessLevel = Column(Enum(accessLevel), nullable=False)
    accountCreated = Column(DateTime)

    #items = relationship("Item", back_populates="owner")

class Place(Base):
    __tablename__ = "places"

    placeID = Column(Integer, primary_key=True)
    posterID = Column(String, ForeignKey("users.username"))
    thumbnails = Column(List[URL], nullable=False)
    location = Column(Geometry('POINT'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    

    #owner = relationship("User", back_populates="items")

class Comment(Base):
    __tablename__ = "comments"

    commentID = Column(Integer, primary_key=True)
    placeID = Column(Integer, ForeignKey("places.placeID"))
    rating = Column(Integer, nullable=False)
    username = Column(String, ForeignKey("users.username"))
