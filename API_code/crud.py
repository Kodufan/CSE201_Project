from datetime import date, datetime, timedelta
import hashlib
import os
import random
import string
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from config import STATIC_FILES_DIRECTORY

import models
import schemas
from schemas import accessLevel, tokenType
from config import ACCESS_TOKEN_DELTA_MINUTES, TOKEN_LENGTH, SERVER_IP

# =============================================================================== USERS

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_from_token(db: Session, token: str):
    get_token = get_token_by_token(db, token)
    if get_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")
    if not get_token.expires < datetime.now():
        return get_user(db, refresh_token_by_token(db, token, tokenType.ACCOUNT).username)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expired token")

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.CreateUser):
    
    hashed_password = hash_password(user.rawPassword)
    

    if get_user(db, user.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is taken")

    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        accessLevel=accessLevel.USER, 
        accountCreated=datetime.now()  
    )

    db.add(db_user)
    db.commit()
        
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, username: str):
    db.delete(get_user(db, username=username))
    db.commit()

def set_user_perms(db: Session, username: str, accessLevel: accessLevel):
    db_user = get_user(db, username=username)

    if db_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    db_user.accessLevel = accessLevel
    db.commit()
    db.refresh(db_user)
    return db_user


# =============================================================================== SECURITY


def hash_password(password: str):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_token_by_user(db: Session, username: str, type: models.tokenType):
    return db.query(models.Token).filter(models.Token.username == username).first()

def get_token_by_token(db: Session, token: str):
    return db.query(models.Token).filter(models.Token.token == token).first()

def delete_token(db: Session, username: str, type:models.tokenType):
    db.delete(get_token_by_user(db, username, type))
    db.commit()

def make_random_string(length: int):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(length))

def create_token(db: Session, username: str, type: models.tokenType):

    token = ''

    # If user token already exists, delete and continue
    if get_token_by_user(db, username, type) is not None:
        delete_token(db, username, type)

    # If user does not exist, throw error
    if get_user(db, username) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    db_token = models.Token(
        username=username,
        type=type,
        token=token,
        expires=(datetime.now() + timedelta(minutes=ACCESS_TOKEN_DELTA_MINUTES))
    )

    # Makes sure that it never uses the same token more than once in the DB.
    while True:
        db_token.token = make_random_string(TOKEN_LENGTH)
        try:
            db.add(db_token)
            db.commit()
            return db_token.token
        except:
            pass

def refresh_token_by_token(db: Session, token: str, type: tokenType):
    db_token = db.query(models.Token).filter(models.Token.token == token).first()
    if db_token.expires < datetime.now():
        return
    db_token.expires = datetime.now() + timedelta(minutes=ACCESS_TOKEN_DELTA_MINUTES)
    db.commit()
    return db_token

def refresh_token_by_user(db: Session, user: schemas.InternalUser):
    db_token = db.query(models.Token).filter(models.Token.username == user.username).first()
    if db_token.expires < datetime.now() or type == tokenType.PASSRESET:
        return
    db_token.expires = datetime.now() + timedelta(minutes=ACCESS_TOKEN_DELTA_MINUTES)
    db.commit()
    return db_token


# =============================================================================== PLACES


def create_place(db: Session, place: schemas.SetPlace, user: schemas.User):
    internalUser = get_user(db, user.username)
    isStaff = internalUser.accessLevel != accessLevel.USER
    
    db_place = models.Place(
        posterID=user.username,
        plusCode=place.plusCode,
        friendlyName=place.friendlyName,
        country=place.country,
        description=place.description,
        isvisible=isStaff,
        rating=0
    )

    db.add(db_place)
    db.commit()


    return db_place

def get_place(db: Session, placeID: int):
    place = db.query(models.Place).filter(models.Place.placeID == placeID).first()

    if place is not None:
        returnPlace = schemas.GetPlace(
                placeID=place.placeID,
                posterID=place.posterID,
                plusCode=place.plusCode,
                friendlyName=place.friendlyName,
                country=place.country,
                description=place.description,
                rating=place.rating,
                thumbnails=db.query(models.Thumbnail).filter(models.Thumbnail.placeID == placeID).all(),
                comments=db.query(models.Comment).filter(models.Comment.placeID == placeID).all()
            )
        return returnPlace

def get_places(db: Session, skip: int = 0, limit: int = 100):
    #TODO: Implement ability to get places by a certain location
    places = db.query(models.Place).order_by(desc('rating')).offset(skip).limit(limit).all()
    list_of_places = list()
    for i in places:
        list_of_places.append(schemas.GetPlace(
            placeID=i.placeID,
            posterID=i.posterID,
            plusCode=i.plusCode,
            friendlyName=i.friendlyName,
            country=i.country,
            description=i.description,
            rating=i.rating,
            thumbnails=db.query(models.Thumbnail).filter(models.Thumbnail.placeID == i.placeID).all(),
            comments=db.query(models.Comment).filter(models.Comment.placeID == i.placeID).all()
        ))
    return list_of_places

def delete_place(db: Session, placeID: int):
    thumbnails = get_thumbnails_from_place(db, placeID)
    for thumbnail in thumbnails:
        os.remove(thumbnail.internalURL)
    db.delete(get_place(db, placeID=placeID))
    db.commit()


# =============================================================================== THUMBNAILS

def add_thumbnail_urls(db: Session, urls: List[str], placeID: int, uploader: schemas.InternalUser):
    
    place = db.query(models.Place).filter(models.Place.placeID == placeID).first()

    if place is None:
        return

    for image in urls:
    
        db_thumbnail = models.Thumbnail(
            uploader=uploader.username,
            placeID=placeID,
            internalURL=STATIC_FILES_DIRECTORY + str(placeID) + "/" + image,
            externalURL=SERVER_IP  + "usercontent/" + str(placeID) + "/" + image,
            uploadDate=datetime.now()
        )

        db.add(db_thumbnail)
    db.commit()
    db.refresh(place)


    return get_place(db, placeID)

def get_thumbnail_urls(db: Session, placeID: int):
    result = list()
    thumbnails = db.query(models.Thumbnail).filter(models.Thumbnail.placeID == placeID).all()

    for url in thumbnails:
        result.append(url.externalURL)
    return result

def get_thumbnails_from_place(db: Session, placeID: int):
    return db.query(models.Thumbnail).filter(models.Thumbnail.placeID == placeID).all()

def get_thumbnail(db: Session, imageID: int):
    return db.query(models.Thumbnail).filter(models.Thumbnail.imageID == imageID).first()

def delete_thumbnail(db: Session, imageID: int):
    image = get_thumbnail(db, imageID)
    os.remove(image.internalURL)

    # Throws weird exception. Not vital to functionality to include
    # path = STATIC_FILES_DIRECTORY = int(image.placeID)
    # if not any(os.scandir(path)):
    #     os.rmdir(path)

    db.delete(get_thumbnail(db, imageID))
    db.commit()
# =============================================================================== COMMENTS


