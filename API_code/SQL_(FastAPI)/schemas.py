from lib2to3.pytree import Base
from datetime import datetime
import this
from pydantic import BaseModel
from yarl import URL
from typing import Optional, List
import enum

class accessLevel(str, enum.Enum):
    User = "User"
    #Moderator = "Moderator"
    Admin = "Admin"

class Comment(BaseModel):
    replyTo: this
    rating: int
    username: str
    commentBody: str
    timePosted: datetime
    timeEdited: datetime

class Location(BaseModel):
    latitude: float
    longitude: float
    country: Optional[str]
    address: Optional[str]
    comments: List[Comment]
    rating: float

class User(BaseModel):
    username: str
    hashedPassword: str
    accessLevel: accessLevel
    accountCreated: datetime

class CreateUser(User):
    rawPassword: str

class Place(BaseModel):
    thumbnails: List[URL]



