import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class accessLevel(str, enum.Enum):
    USER = "User"
    MODERATOR = "Moderator"
    ADMIN = "Admin"

class tokenType(str, enum.Enum):
    ACCOUNT = "Account"
    PASSRESET = "PassReset"
    VERIFICATION = "Verification"

class placeOrder(str, enum.Enum):
    POPULARITY = "Popularity"
    DISTANCE = "Distance"

class visibility(int, enum.Enum):
    ALL = -1
    VERIFIED = 1
    UNVERIFIED = 0

class SetRating(BaseModel):
    placeID: int
    ratingValue: int
    commentBody: Optional[str]

    class Config:
        orm_mode=True

class GetRating(SetRating):
    ratingID: int
    username: str
    timePosted: datetime
    timeEdited: datetime

class PatchRating(BaseModel):
    ratingID: int
    ratingValue: Optional[int]
    commentBody: Optional[str]

    class Config:
        orm_mode=True

class Thumbnail(BaseModel):
    imageID: int
    uploader: str
    placeID: int
    externalURL: str
    uploadDate: datetime

    class Config:
        orm_mode=True

class InternalThumbnail(Thumbnail):
    internalURL: str

class SetPlace(BaseModel):
    plusCode: str
    friendlyName: str
    country: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode=True

class PatchPlace(BaseModel):
    placeID: int
    plusCode: Optional[str]
    friendlyName: Optional[str]
    country: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode=True

class GetPlace(SetPlace):
    placeID: int
    posterID: str
    rating: float
    thumbnails: Optional[List[Thumbnail]]
    comments: Optional[List[GetRating]]

class InternalPlace(GetPlace):
    isvisible: bool

class User(BaseModel):
    username: str
    
    class Config:
        orm_mode=True

class UserInfo(User):
    ratings: Optional[List[GetRating]]
    places: Optional[List[GetPlace]]

class InternalUser(UserInfo):
    email: str
    verified: bool
    accessLevel: accessLevel
    accountCreated: datetime

class CreateUser(User):
    email: str
    rawPassword: str

class StoreUser(User):
    hashedPassword: str

    