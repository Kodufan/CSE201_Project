from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
import enum

class accessLevel(str, enum.Enum):
    USER = "User"
    #MODERATOR = "Moderator"
    ADMIN = "Admin"

class Comment(BaseModel):
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
    accessLevel: accessLevel
    accountCreated: datetime

    class Config:
        orm_mode=True

class CreateUser(User):
    rawPassword: str

class StoreUser(User):
    hashedPassword: str

class Place(BaseModel):
    thumbnails: List[str]