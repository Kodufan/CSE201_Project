from datetime import datetime
from fastapi import File
from pydantic import BaseModel
from typing import Optional, List
import enum

class accessLevel(str, enum.Enum):
    USER = "User"
    MODERATOR = "Moderator"
    ADMIN = "Admin"

class Rating(BaseModel):
    rating: int
    username: str

    class Config:
        orm_mode=True

class Comment(Rating):
    commentBody: str
    timePosted: datetime
    timeEdited: datetime

class User(BaseModel):
    username: str
    
    class Config:
        orm_mode=True

class InternalUser(User):
    accessLevel: accessLevel
    accountCreated: datetime

class CreateUser(User):
    rawPassword: str

class StoreUser(User):
    hashedPassword: str

class SetPlace(BaseModel):
    plusCode: str
    friendlyName: str
    country: Optional[str]
    description: Optional[str]
    rating: float

    class Config:
        orm_mode = True
    

class GetPlace(SetPlace):
    placeID: int
    posterID: str
    thumbnails: Optional[List[str]]
    comments: Optional[List[Comment]]