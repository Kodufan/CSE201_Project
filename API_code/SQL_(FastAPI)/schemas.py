import enum
from datetime import datetime
from typing import List, Optional

from fastapi import File
from pydantic import BaseModel


class accessLevel(str, enum.Enum):
    USER = "User"
    MODERATOR = "Moderator"
    ADMIN = "Admin"

class tokenType(str, enum.Enum):
    ACCOUNT = "Account"
    PASSRESET = "PassReset"

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

class Rating(BaseModel):
    ratingID: int
    placeID: int
    ratingValue: int
    username: str
    timePosted: datetime
    timeEdited: datetime

    class Config:
        orm_mode=True

class Comment(Rating):
    commentBody: str

class Thumbnail(BaseModel):
    imageURL: str
    uploader: str
    placeID: int
    uploadDate: datetime

    class Config:
        orm_mode=True

class SetPlace(BaseModel):
    plusCode: str
    friendlyName: str
    country: Optional[str]
    description: Optional[str]
    rating: float

    class Config:
        orm_mode=True
    
class GetPlace(SetPlace):
    placeID: int
    posterID: str
    thumbnails: Optional[List[Thumbnail]]
    comments: Optional[List[Comment]]