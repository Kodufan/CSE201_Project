import hashlib
import os
import random
import string
from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException, status

# Installed from PIP. More information at https://www.sqlalchemy.org/
from sqlalchemy import desc
from sqlalchemy.orm import Session

import models
import schemas
from config import (ACCESS_TOKEN_DELTA_MINUTES, SERVER_IP,
                    STATIC_FILES_DIRECTORY, TOKEN_LENGTH)
from latlonhelper import distance

# Taken from https://github.com/google/open-location-code
# License information can be found in openlocationcode.py
from openlocationcode import decode, isFull
from schemas import PatchPlace, accessLevel, tokenType, visibility

# =============================================================================== USERS

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_from_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_info(db: Session, username: str):
    db_user = get_user(db, username)
    if db_user is not None:
        return_user = schemas.InternalUser(
                username=db_user.username,
                email=db_user.email,
                verified=db_user.verified,
                images=get_thumbnails_from_user(db, db_user),
                ratings=get_user_ratings(db, db_user),
                places=get_places_from_user(db, db_user),
                accessLevel=db_user.accessLevel,
                accountCreated=db_user.accountCreated
            )
        return return_user

def get_user_from_token(db: Session, token: str):
    return get_user(db, refresh_token_by_token(db, token).email)

def get_users(db: Session, skip: int = 0, limit: int = 100):
    users = db.query(models.User).offset(skip).limit(limit).all()
    output = list()
    for user in users:
        output.append(get_user_info(db, user.email))
    return output

def create_user(db: Session, user: schemas.CreateUser):
    if not user.email or not user.username or not user.rawPassword:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing fields")
    hashed_password = hash_password(user.rawPassword)

    if get_user(db, user.email) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is taken")
    
    if get_user_from_username(db, user.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is taken")

    db_user = models.User(
        username=user.username, 
        email=user.email,
        verified=False,
        hashed_password=hashed_password, 
        accessLevel=accessLevel.USER, 
        accountCreated=datetime.now()  
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, email: str):
    db.delete(get_user(db, email=email))
    db.commit()

def set_user_perms(db: Session, email: str, accessLevel: accessLevel):
    db_user = get_user(db, email=email)

    if db_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    db_user.accessLevel = accessLevel
    db.commit()
    db.refresh(db_user)
    return db_user

def change_username(db: Session, user: schemas.InternalUser, username: str):
    db_user = get_user(db, user.email)
    db_user.username = username
    db.commit()
    db.refresh(db_user)
    return db_user

# =============================================================================== PLACES


def create_place(db: Session, place: schemas.SetPlace, user: schemas.InternalUser):
    isStaff = user.accessLevel != accessLevel.USER
    
    if not isFull(place.plusCode):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PlusCode")

    db_place = models.Place(
        posterID=user.username,
        plusCode=place.plusCode,
        friendlyName=place.friendlyName,
        country=place.country,
        description=place.description,
        verified=isStaff,
        rating=-1
    )

    db.add(db_place)
    db.commit()


    return db_place

def get_place(db: Session, placeID: int, ):
    place = db.query(models.Place).filter(models.Place.placeID == placeID).first()

    if place is not None:
        returnPlace = schemas.InternalPlace(
                placeID=place.placeID,
                posterID=place.posterID,
                plusCode=place.plusCode,
                friendlyName=place.friendlyName,
                country=place.country,
                description=place.description,
                rating=place.rating,
                thumbnails=get_thumbnails_from_place(db, placeID, False),
                comments=db.query(models.Comment).filter(models.Comment.placeID == placeID).all(),
                isvisible=place.verified
            )
        return returnPlace

def get_place_pointer(db: Session, placeID: int):
    return db.query(models.Place).filter(models.Place.placeID == placeID).first()

def get_places_by_popularity(db: Session, skip: int = 0, limit: int = 100, visibility = visibility):
    query = db.query(models.Place).order_by(desc('rating'))
    if visibility != visibility.ALL:
        query = query.filter(models.Place.verified == (True if visibility == 1 else False))
    else: 
        query = query.order_by(desc('rating'))
    places = query.offset(skip).limit(limit).all()
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
            thumbnails=get_thumbnails_from_place(db, i.placeID, False),
            comments=db.query(models.Comment).filter(models.Comment.placeID == i.placeID).all()
        ))
    return list_of_places

def get_places_by_distance(db: Session, latitude: int, longitude: int, skip: int = 0, limit: int = 100, visibility = visibility):
    query = db.query(models.Place)

    if visibility != visibility.ALL:
        query = query.filter(models.Place.verified == (True if visibility == 1 else False))
    else: 
        query = query.order_by(desc('rating'))
    places = query.offset(skip).limit(limit).all()
    places_dict_unsorted = dict()
    places_dict_sorted = dict()

    for i in places:
        position = decode(i.plusCode).latlng()
        placeLat = position[0]
        placeLon = position[1]
        dist = distance(latitude, longitude, placeLat, placeLon)
        new_place = schemas.GetPlace(
            placeID=i.placeID,
            posterID=i.posterID,
            plusCode=i.plusCode,
            friendlyName=i.friendlyName,
            country=i.country,
            description=i.description,
            rating=i.rating,
            thumbnails=get_thumbnails_from_place(db, i.placeID, False),
            comments=db.query(models.Comment).filter(models.Comment.placeID == i.placeID).all()
        )
        places_dict_unsorted[dist] = new_place
    for i in sorted(places_dict_unsorted):
        places_dict_sorted[i] = places_dict_unsorted[i]
    return_list = list(places_dict_sorted.values())
    return return_list

def get_places_from_user(db: Session, user: schemas.InternalUser):
    db_places = db.query(models.Place).order_by(desc('rating')).filter(models.Place.posterID == user.username).all()
    return_places = list()

    for i in db_places:
        return_places.append(get_place(db, i.placeID))
    return return_places

def get_place_names(db: Session, name: str):
    db_places = db.query(models.Place).order_by(desc('rating')).filter(models.Place.friendlyName.contains(name)).filter(models.Place.verified == 1).all()
    return_places = list()

    for i in db_places:
        new_place = schemas.SearchPlace(
            placeID=i.placeID,
            friendlyName=i.friendlyName
        )
        return_places.append(new_place)
    return return_places

def update_place(db: Session, place: PatchPlace):
    db_place = db.query(models.Place).filter(models.Place.placeID == place.placeID).first()
    db_place.plusCode = place.plusCode
    db_place.friendlyName = place.friendlyName
    db_place.country = place.country
    db_place.description = place.description

    db.commit()
    return get_place(db, db_place.placeID)

def set_place_visibility(db: Session, placeID: int, visibility: bool):
    place = db.query(models.Place).filter(models.Place.placeID == placeID).first()
    place.verified = visibility
    db.commit()

def delete_place(db: Session, placeID: int):
    thumbnails = get_thumbnails_from_place(db, placeID)
    for thumbnail in thumbnails:
        os.remove(thumbnail.internalURL)
    db.delete(get_place_pointer(db, placeID=placeID))
    db.commit()


# =============================================================================== THUMBNAILS

def add_thumbnail_urls(db: Session, urls: List[str], placeID: int, uploader: schemas.InternalUser):
    place = db.query(models.Place).filter(models.Place.placeID == placeID).first()

    isverified = uploader.accessLevel != accessLevel.USER
    if place is None:
        return

    for image in urls:
        db_thumbnail = models.Thumbnail(
            uploader=uploader.username,
            verified=isverified,
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

def get_thumbnails_from_place(db: Session, placeID: int, show_unverified: bool):
    query = db.query(models.Thumbnail).filter(models.Thumbnail.placeID == placeID)
    if not show_unverified:
        query = query.filter(models.Thumbnail.verified == True)
    return query.all()

def get_thumbnails_from_user(db: Session, user: schemas.InternalUser):
    return db.query(models.Thumbnail).filter(models.Thumbnail.uploader == user.username).filter(models.Thumbnail.verified == True).all()

def get_thumbnail(db: Session, imageID: int):
    return db.query(models.Thumbnail).filter(models.Thumbnail.imageID == imageID).first()

def set_thumbnail_visibility(db: Session, imageID: int, visibility: bool):
    image = db.query(models.Thumbnail).filter(models.Thumbnail.imageID == imageID).first()
    image.verified = visibility
    db.commit()

def get_unverified_thumbnails(db: Session, skip: int = 0, limit: int = 100):
    query = db.query(models.Thumbnail)
    images = query.filter(models.Thumbnail.verified == False).offset(skip).limit(limit).all()
    return images

def delete_thumbnail(db: Session, imageID: int):
    image = get_thumbnail(db, imageID)
    os.remove(image.internalURL)

    path = STATIC_FILES_DIRECTORY + str(image.placeID)

    if not any(os.scandir(path)):
        os.rmdir(path)
    db.delete(get_thumbnail(db, imageID))
    db.commit()

# =============================================================================== COMMENTS

def create_rating(db: Session, rating: schemas.SetRating, user: schemas.InternalUser):
    current_time = datetime.now()
    db_rating = models.Comment(
        placeID=rating.placeID,
        ratingValue=rating.ratingValue,
        username=user.username,
        commentBody=rating.commentBody,
        timePosted=current_time,
        timeEdited=current_time,
    )

    db.add(db_rating)
    db.commit()
    update_score(db, rating.placeID)

    return db_rating

def update_rating(db: Session, rating: schemas.GetRating):
    db_rating = db.query(models.Comment).filter(models.Comment.placeID == rating.placeID).first()
    db_rating.commentBody = rating.commentBody
    db_rating.ratingValue = rating.ratingValue
    db_rating.timeEdited = datetime.now()

    db.commit()
    return db_rating

def get_rating(db: Session, ratingID: int):
    rating = db.query(models.Comment).filter(models.Comment.ratingID == ratingID).first()

    if rating is not None:
        return_rating = schemas.GetRating(
                ratingID=rating.ratingID,
                placeID=rating.placeID,
                ratingValue=rating.ratingValue,
                commentBody=rating.commentBody,
                username=rating.username,
                timePosted=rating.timePosted,
                timeEdited=rating.timeEdited
            )
        return return_rating

def get_rating_pointer(db: Session, ratingID = int):
    return db.query(models.Comment).filter(models.Comment.ratingID == ratingID).first()

def get_user_ratings(db: Session, user: schemas.InternalUser):
    return db.query(models.Comment).filter(models.Comment.username == user.username).all()

def delete_rating(db: Session, ratingID: int):
    rating = get_rating_pointer(db, ratingID)
    placeID = rating.placeID
    db.delete(rating)
    db.commit()
    update_score(db, placeID)

def update_score(db: Session, placeID: int):
    ratings = db.query(models.Comment).filter(models.Comment.placeID == placeID).all()
    
    ratingValues = list()
    for i in ratings:
        ratingValues.append(i.ratingValue)

    sum = 0
    for i in ratingValues:
        sum += i

    place = db.query(models.Place).filter(models.Place.placeID == placeID).first()
    if len(ratingValues) == 0:
        place.rating = -1
    else:
        place.rating = round((sum / (len(ratingValues))), 1)
    db.commit()


# =============================================================================== SECURITY


def hash_password(password: str):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_token_by_user(db: Session, email: str, type: models.tokenType):
    return db.query(models.Token).filter(models.Token.email == email).filter(models.Token.type == type).first()

def get_token_by_token(db: Session, token: str):
    return db.query(models.Token).filter(models.Token.token == token).first()

def delete_token(db: Session, email: str, type:models.tokenType):
    db.delete(get_token_by_user(db, email, type))
    db.commit()

def make_random_string(length: int):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(length))

def create_token(db: Session, email: str, type: models.tokenType):
    token = ''

    # If user token already exists, delete and continue
    if get_token_by_user(db, email, type) is not None:
        delete_token(db, email, type)

    # If user does not exist, throw error
    if get_user(db, email) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    db_token = models.Token(
        email=email,
        type=type,
        token=token
    )

    if type == tokenType.ACCOUNT:
        db_token.expires = datetime.now() + timedelta(minutes=ACCESS_TOKEN_DELTA_MINUTES)
    if type == tokenType.PASSRESET:
        db_token.expires = datetime.now() + timedelta(days=1)
    if type == tokenType.VERIFICATION:
        # This value isn't used as verification tokens don't check if expired.
        db_token.expires = datetime.now()

    # Makes sure that it never uses the same token more than once in the DB.
    while True:
        db_token.token = make_random_string(TOKEN_LENGTH)
        try:
            db.add(db_token)
            db.commit()
            return db_token.token
        except:
            pass

def refresh_token_by_token(db: Session, token: str):
    db_token = get_token_by_token(db, token)
    if db_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")

    if db_token.expires < datetime.now() and db_token.type == tokenType.ACCOUNT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    else:
        db_token.expires = datetime.now() + timedelta(minutes=ACCESS_TOKEN_DELTA_MINUTES)
        db.commit()
    return db_token

def refresh_token_by_user(db: Session, user: schemas.InternalUser):
    db_token = get_token_by_user(db, user.email, tokenType.ACCOUNT)
    if db_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")

    if db_token.expires < datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    else:
        db_token.expires = datetime.now() + timedelta(minutes=ACCESS_TOKEN_DELTA_MINUTES)
        db.commit()
        return db_token

def verify_account(db: Session, token: str):
    user = get_user_from_token(db, token)
    token_obj = get_token_by_token(db, token)
    user.verified = True
    db.delete(token_obj)
    db.commit()

def reset_password(db: Session, password: str, token: str):
    user = get_user_from_token(db, token)
    user.hashed_password = hash_password(password)
    db.commit()
