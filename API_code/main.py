from importlib.resources import path
import os
import shutil
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pathlib2 import PurePosixPath
from sqlalchemy.orm import Session

import crud
from config import STATIC_FILES_DIRECTORY
from crud import *
from database import SessionLocal, engine
from models import *
from schemas import *
from schemas import accessLevel, tokenType

tags_metadata = [
    {
        "name": "Users",
        "description": "Operations with users.",
    },
    {
        "name": "Places",
        "description": "Operations with places.",
    },
    {
        "name": "Thumbnails",
        "description": "Operations with thumbnails.",
    },
    {
        "name": "Comments",
        "description": "Operations with comments.",
    },
    {
        "name": "Security",
        "description": "Operations with security.",
    },
    {
        "name": "Debug",
        "description": "Used for debug. Should never use for production",
    },
]


models.Base.metadata.create_all(bind=engine)
app = FastAPI(openapi_tags=tags_metadata)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

#TODO: add trycatch to make folder
app.mount("/usercontent", StaticFiles(directory=STATIC_FILES_DIRECTORY), name="usercontent")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security

def decode_token(db, token: str):
    return crud.get_user_from_token(db, token)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = decode_token(db, token)
    return user

async def write_file(filePath: Path, file: UploadFile):
    if not filePath.exists():
        filePath.mkdir()

    with open(filePath / file.filename, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    return file.filename

async def write_files(filePath: Path, files: List[UploadFile], existing_urls: List[str]):
    urls = list()
    for file in files:
        file_name = ''

        while True:
            file_name = crud.make_random_string(10)
            if file_name not in existing_urls:
                break
        file.filename = file_name + PurePosixPath(file.filename).suffix
        urls.append(await write_file(filePath, file))
    return urls
# Endpoints

# =============================================================================== USERS


@app.post("/createUser", response_model=schemas.InternalUser, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    """
    Create a user with all the information:

    - username: this unique identifier must not exceed 20 characters
    - rawpassword: this will be the password. Stored hashed with SHA-256
    """
    return crud.create_user(db, user)

@app.post("/setUserPerms", response_model=schemas.User, status_code=status.HTTP_200_OK, tags=["Users"])
def set_perms(username: str, accessLevel: accessLevel, db: Session = Depends(get_db), callingUser: schemas.InternalUser = Depends(get_current_user)):
    """
    Sets the permissions of a user:

    - username: the user whos permission will be changed
    - accessLevel: the new permission level of the user, either User, Moderator

    Note: Admins cannot change the permission level of other admins or make other users admin. Only admins can use this command, otherwise it will respond with a 401. 
    """
    user = crud.get_user(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Only sets perms if the logged in user is admin. Doesn't allow setting other users to admin. Doesn't allow demoting other admins including self
    if callingUser.accessLevel == accessLevel.ADMIN and not accessLevel == accessLevel.ADMIN and not user.accessLevel == accessLevel.ADMIN:
        set_user_perms(db, username, accessLevel)
    else:
        raise HTTPException(status_code=401, detail="Forbidden") 

@app.get("/users/", response_model=List[schemas.InternalUser], tags=["Users"])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Gets a list of users and their information

    - skip: will offset the users returned
    - limit: will return either this amount of users or the number of users after the skip offset, whichever is smaller
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@app.get("/user/{username}", response_model=schemas.InternalUser, tags=["Users"])
def get_user(username: str, db: Session = Depends(get_db)):
    """
    Gets a user's information

    - username: the username to fetch

    Note: Returns a 404 if the user doesn't exist
    """
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/user/", status_code=200, tags=["Users"])
def delete_user(user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes a user

    - username: the username to fetch

    Note: Returns a 404 if the user doesn't exist. Returns a 403 if the user is trying to delete someone else and is not an admin. Admins can delete any user that isn't an admin, but can delete themselves.
    """
    db_user = crud.get_user(db, username=user.username)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if db_user == user:
        crud.delete_user(db, username=user.username)
    elif user.accessLevel == accessLevel.ADMIN and db_user.accessLevel != accessLevel.ADMIN:
        crud.delete_user(db, username=user.username)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


# =============================================================================== PLACES


@app.post("/createPlace", response_model=schemas.GetPlace, status_code=status.HTTP_201_CREATED, tags=["Places"])
def create_place(place: SetPlace, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create a place with all the information:

    - plusCode: Unique identifier for use with Google Maps. Cannot exceed 100 characters.
    - friendlyName: Coloquial name of location. Cannot exceed 100 characters.
    - country: 2 or 3 character ISO country code. Cannot exceed 5 characters.
    - description: Small bio of location. Cannot exceed 1,000 characters.
    """
    return crud.create_place(db, place, user)

@app.get("/place/{placeID}", response_model=schemas.GetPlace, tags=["Places"])
def get_place(placeID: int, db: Session = Depends(get_db)):
    """
    Gets the information of a palce

    - placeID: ID of the place to retrieve. Will always be an integer

    Note: Returns a 404 if the place doesn't exist
    """
    db_place = crud.get_place(db, placeID=placeID)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return db_place

@app.get("/places/", response_model=List[schemas.GetPlace], tags=["Places"])
def list_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    places = get_places(db, skip=skip, limit=limit)
    return places

@app.delete("/place/{placeID}", status_code=status.HTTP_200_OK, tags=["Places"])
def delete_place(placeID: int, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):

    if user.accessLevel == accessLevel.ADMIN:
        db_place = crud.get_place(db, placeID=placeID)
        if db_place is None:
            raise HTTPException(status_code=404, detail="Place not found")
        crud.delete_user(db, placeID=placeID)
    else:
        raise HTTPException(status_code=401, detail="Forbidden")


# =============================================================================== THUMBNAILS


@app.post("/uploadThumbnails/", status_code=status.HTTP_201_CREATED, tags=["Thumbnails"])
async def create_upload_file(files: List[UploadFile], placeID: int, db: Session = Depends(get_db), user: schemas.InternalUser = Depends(get_current_user)):
    place = crud.get_place(db, placeID)
    if place is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    path = Path(STATIC_FILES_DIRECTORY + str(placeID))
    
    if place.posterID == user.username or user.accessLevel == accessLevel.ADMIN:
        return add_thumbnail_urls(db, await write_files(path, files, get_thumbnail_urls(db, placeID)), placeID, user)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

@app.get("/thumbnails/{placeID}", response_model=List[schemas.Thumbnail], tags=["Thumbnails"])
def get_thumbnails_from_place(placeID: int, db: Session = Depends(get_db)):
    return crud.get_thumbnails_from_place(db, placeID=placeID)
    
@app.delete("/thumbnails/{thumbnailID}", status_code=status.HTTP_200_OK, tags=["Thumbnails"])
def delete_thumbnail(imageID: int, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    thumbnail = get_thumbnail(db, imageID)

    if thumbnail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

    place = get_place(thumbnail.placeID, db)

    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found // YOU SHOULD NEVER SEE THIS")

    if user.accessLevel != accessLevel.USER or user.username == place.posterID:
        crud.delete_thumbnail(db, imageID)
    else:
        raise HTTPException(status_code=401, detail="Forbidden")

# =============================================================================== SECURITY


@app.post("/login", tags=["Security"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user(db, form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    hashed_password = crud.hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    access_token = create_token(db, username=form_data.username, type=tokenType.ACCOUNT)

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/refreshToken", response_model=schemas.InternalUser, tags=["Security"])
async def login(user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not crud.refresh_token_by_user(db, user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")


# =============================================================================== DEBUG

@app.get("/", tags=["Debug"])
async def debug():
    path = os.getcwd()
    print("Current directory", path)
    print()
    parent = os.path.dirname(path)
    print("Parent directory", parent)
