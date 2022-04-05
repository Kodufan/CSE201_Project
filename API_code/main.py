import os
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import crud
from apihelper import (decode_token, get_db, send_reset_email,
                       send_verification_email, write_files)
from config import STATIC_FILES_DIRECTORY
from crud import *
from database import engine
from models import *
from openlocationcode import isFull
from schemas import *
from schemas import accessLevel, placeOrder, tokenType, visibility, Token

# Dict of tags and their descriptions to break the OpenAPI docs into sections
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
        "name": "Ratings",
        "description": "Operations with ratings.",
    },
    {
        "name": "Moderation",
        "description": "Operations with moderation.",
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

# Creates database connections
models.Base.metadata.create_all(bind=engine)

# Initializes the application
app = FastAPI(openapi_tags=tags_metadata)

# Accepted cors origins
origins = ["*"]

# Adds cors to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initializes OAuth2 and tells the OpenAPI docs to look at the /login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Mounts /usercontent as a static directory at STATIC_FILES_DIRECTORY in config.py. If directory does not exist, make it and mount it
try:
    app.mount("/usercontent", StaticFiles(directory=STATIC_FILES_DIRECTORY), name="usercontent")
except:
    os.mkdir(STATIC_FILES_DIRECTORY)
    app.mount("/usercontent", StaticFiles(directory=STATIC_FILES_DIRECTORY), name="usercontent")


# This method returns the current user from a token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = decode_token(db, token)
    if user.verified == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account has not been verified")
    return user



# =============================================================================== USERS


@app.post("/createUser", response_model=schemas.InternalUser, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    """
    Create a user with all the information:

    - username: this must not exceed 20 characters or match another username
    - email: this unique identifier must not exceed 100 characters
    - rawpassword: this will be the password. Stored hashed with SHA-256

    Note: Returns a 404 if either the username or emails are taken.
    """
    user = crud.create_user(db, user)
    token = crud.create_token(db, user.email, tokenType.VERIFICATION)
    try:
        send_verification_email(user, token)
        pass
    except:
        crud.delete_user(db, user.email)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Email could not be sent")
    return user

@app.post("/setUserPerms", response_model=schemas.User, status_code=status.HTTP_200_OK, tags=["Users"])
def set_perms(username: str, accessLevel: accessLevel, callingUser: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
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

@app.post("/changeUsername", response_model=schemas.UserInfo, status_code=status.HTTP_200_OK, tags=["Users"])
def change_username(new_username: str, email: str, callingUser: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Changes a user's username:

    - email: the user whos name will be changed
    - new_username: the new username it will be set to

    Note: All users can change their own usernames. Staff can change the usernames of USER users.
    """
    user = crud.get_user(db, email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.username == new_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a new username") 
    if crud.get_user_from_username(db, new_username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken") 
    

    # Only sets perms if the logged in user is admin. Doesn't allow setting other users to admin. Doesn't allow demoting other admins including self
    if (callingUser.email != user.email and callingUser.accessLevel == accessLevel.USER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden") 
    return crud.change_username(db, user, new_username)

@app.get("/user/{username}", response_model=schemas.InternalUser, tags=["Users"])
def get_user(username: str, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Gets a user's information

    - username: the username to fetch

    Note: Returns a 404 if the user doesn't exist or 403 if user is not an admin
    """
    if user.accessLevel != accessLevel.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    db_user = crud.get_user_info(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/", response_model=List[schemas.InternalUser], tags=["Users"])
def list_users(skip: int = 0, limit: int = 100, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Gets a list of users and their information

    - skip: will offset the users returned
    - limit: will return either this amount of users or the number of users after the skip offset, whichever is smaller

    Note: Returns a 403 if user is not an admin
    """
    if user.accessLevel != accessLevel.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    users = get_users(db, skip=skip, limit=limit)
    return users

@app.delete("/user/", status_code=200, tags=["Users"])
def delete_user(email: str, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes a user

    - email: the email of the account to fetch

    Note: Returns a 404 if the user doesn't exist. Returns a 403 if the user is trying to delete someone else and is not an admin. Admins can delete any user that isn't an admin, but can delete themselves.
    """
    db_user = crud.get_user(db, email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if db_user == user:
        crud.delete_user(db, email=user.email)
    elif user.accessLevel == accessLevel.ADMIN and db_user.accessLevel != accessLevel.ADMIN:
        crud.delete_user(db, email=user.email)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


# =============================================================================== PLACES


@app.post("/create/place", response_model=schemas.GetPlace, status_code=status.HTTP_201_CREATED, tags=["Places"])
def create_place(place: SetPlace, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create a place with all the information:

    - plusCode: Unique identifier for use with Google Maps. Cannot exceed 100 characters.
    - friendlyName: Coloquial name of location. Cannot exceed 100 characters.
    - country: 2 or 3 character ISO country code. Cannot exceed 5 characters.
    - description: Small bio of location. Cannot exceed 1,000 characters.
    """
    return crud.create_place(db, place, user)

@app.get("/place/guest/{placeID}", response_model=schemas.GetPlace, tags=["Places"])
def get_place(placeID: int, db: Session = Depends(get_db)):
    """
    Gets the information of a palce

    - placeID: ID of the place to retrieve. Will always be an integer
    - visibility: Determines whether all, verified, or unverified places are displayed

    Note: Returns a 404 if the place doesn't exist. Returns a 403 if place is unverified.
    """
    db_place = crud.get_place(db, placeID=placeID)
    if db_place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    if not db_place.isvisible:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Place not verified")
    return db_place

@app.get("/place/user/{placeID}", response_model=schemas.GetPlace, tags=["Places"])
def get_place(placeID: int, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Gets the information of a palce

    - placeID: ID of the place to retrieve. Will always be an integer
    - visibility: Determines whether all, verified, or unverified places are displayed

    Note: Returns a 404 if the place doesn't exist. Returns a 403 if a user tries to view all or unverified places.
    """
    db_place = crud.get_place(db, placeID=placeID)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    if user.accessLevel == accessLevel.USER:
        if not db_place.isvisible:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Place not verified")
    db_place = crud.get_place(db, placeID=placeID)
    return db_place

@app.get("/places/guest", response_model=List[schemas.GetPlace], tags=["Places"])
def list_places(order: placeOrder, latitude: float = 0, longitude: float = 0, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Gets a list of verified places and their information

    - order: determines if results are ordered by distance or rating
    - skip: will offset the places returned
    - limit: will return either this amount of places or the number of places after the skip offset, whichever is smaller

    Note: If sorting by rating, latitude and longitude are not required.
    """
    if order == placeOrder.POPULARITY:
        places = get_places_by_popularity(db, skip, limit, visibility.VERIFIED)
    else:
        places = get_places_by_distance(db, latitude, longitude, skip, limit, visibility.VERIFIED)
    return places

@app.patch("/place/{placeID}", response_model=GetPlace, tags=["Places"])
async def update_item(patch_place: PatchPlace, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Updates a place

    - placeID: the id to fetch. Will always be an integer
    - plusCode: the optional PlusCode to update. Cannot exceed 100 characters.
    - friendlyName: the optional friendly name to update. Cannot exceed 100 characters.
    - country: the optional country to update. Cannot exceed 5 characters.
    - description: the optional description to update. Cannot exceed 1,000 characters

    Note: Returns a 404 if the place doesn't exist. Returns a 403 if the user is trying to modify someone else's place and is not staff. Staff can modify any place
    """

    if not isFull(patch_place.plusCode):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid PlusCode")
    db_place = crud.get_place(db, patch_place.placeID)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    if user.accessLevel == accessLevel.ADMIN or user.username == db_place.posterID:
        update_data = patch_place.dict(exclude_unset=True)
        updated_place = PatchPlace(**jsonable_encoder(db_place.copy(update=update_data)))
        place = crud.update_place(db, updated_place)
        return place
    else:
        raise HTTPException(status_code=401, detail="Forbidden")

@app.delete("/place/{placeID}", status_code=status.HTTP_200_OK, tags=["Places"])
def delete_place(placeID: int, user: InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes a place

    - placeID: the id to fetch. Will always be an integer

    Note: Returns a 404 if the place doesn't exist. Returns a 403 if the user is trying to delete someone else's place and is not staff. Staff can delete any place
    """
    db_place = crud.get_place(db, placeID)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    if user.accessLevel == accessLevel.ADMIN or db_place.posterID == user.username:
        crud.delete_place(db, placeID=placeID)
    else:
        raise HTTPException(status_code=401, detail="Forbidden")


# =============================================================================== THUMBNAILS


@app.post("/uploadThumbnails/", status_code=status.HTTP_201_CREATED, tags=["Thumbnails"])
async def create_upload_file(files: List[UploadFile], placeID: int, db: Session = Depends(get_db), user: schemas.InternalUser = Depends(get_current_user)):
    """
    Uploads a series of thumbnails

    - files: the series of files to upload
    - placeID: the placeID to associate the uploaded files to. Will always be an integer

    Note: Returns a 404 if the place doesn't exist. Returns a 403 if a user tries to upload images to a place they didn't post. Admins can add images to any place
    """
    place = crud.get_place(db, placeID)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    path = Path(STATIC_FILES_DIRECTORY + str(placeID))
    
    if place.posterID == user.username or user.accessLevel == accessLevel.ADMIN:
        crud.add_thumbnail_urls(db, await write_files(path, files, get_thumbnail_urls(db, placeID)), placeID, user)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

@app.get("/thumbnails/{placeID}", response_model=List[schemas.Thumbnail], tags=["Thumbnails"], deprecated=True)
def get_thumbnails_from_place(placeID: int, db: Session = Depends(get_db)):
    """
    Gets the information of a thumbnail

    - imageID: ID of the image to retrieve. Will always be an integer

    Note: Returns a 404 if the image doesn't exist. Marked deprecated as getting a place also returns a list of thumbnails
    """
    return crud.get_thumbnails_from_place(db, placeID=placeID)
    
@app.delete("/thumbnails/{thumbnailID}", status_code=status.HTTP_200_OK, tags=["Thumbnails"])
def delete_thumbnail(imageID: int, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes a thumbnail

    - imageID: the id of the image to delete. Will always be an integer

    Note: Returns a 404 if the image doesn't exist. Returns a 403 if the user is trying to delete someone else's image and is not staff. Staff can delete any image
    """
    thumbnail = get_thumbnail(db, imageID)

    if thumbnail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

    place = crud.get_place(db, thumbnail.placeID)

    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found // YOU SHOULD NEVER SEE THIS")

    if user.accessLevel != accessLevel.USER or user.username == place.posterID:
        crud.delete_thumbnail(db, imageID)
    else:
        raise HTTPException(status_code=401, detail="Forbidden")


# =============================================================================== RATINGS


@app.post("/create/rating", response_model=schemas.GetRating, status_code=status.HTTP_201_CREATED, tags=["Ratings"])
def create_rating(rating: SetRating, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create a comment with all the information:

    - plusCode: Unique identifier for use with Google Maps. Cannot exceed 100 characters.
    - friendlyName: Coloquial name of location. Cannot exceed 100 characters.
    - country: 2 or 3 character ISO country code. Cannot exceed 5 characters.
    - description: Small bio of location. Cannot exceed 1,000 characters.

    Note: Returns a 400 if the rating value is below 1 or above 5. Returns a 404 if the place being rated doesn't exist. Returns a 403 if user has already rated the place
    """
    # Checks if place exists and rating is within range
    place = crud.get_place(db, rating.placeID)
    if rating.ratingValue < 1 or rating.ratingValue > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")
    elif place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Checks if user has rated before
    ratings = get_user_ratings(db, user)
    # Depending on frontend requirements, could replace 400 with automatic rating update
    for i in ratings:
        if i.placeID == rating.placeID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already rated this place")

    return crud.create_rating(db, rating, user)

@app.patch("/rating/{ratingID}", response_model=GetRating, tags=["Ratings"])
async def update_rating(ratingID: int, patch_rating: PatchRating, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Updates a rating

    - ratingID: the id to fetch. Will always be an integer
    - ratingValue: the optional rating to update. Must be between 1 and 5 and an integer.
    - comment: the optional comment body to update. Cannot exceed 1,000 characters.

    Note: Returns a 404 if the rating doesn't exist. Returns a 403 if the user is trying to modify someone else's rating.
    """
    db_rating = crud.get_rating(db, ratingID)
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    if user.username == db_rating.username:
        # Taken from the FastAPI docs regarding partial data updates. Idk how it works but it does
        update_data = patch_rating.dict(exclude_unset=True)
        updated_rating = GetRating(**jsonable_encoder(db_rating.copy(update=update_data)))
        rating = crud.update_rating(db, updated_rating)
        return rating
    else:
        raise HTTPException(status_code=401, detail="Forbidden")

@app.delete("/rating/{ratingID}", status_code=status.HTTP_200_OK, tags=["Ratings"])
def delete_rating(ratingID: int, user: InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Deletes a rating

    - ratingID: the id to fetch. Will always be an integer

    Note: Returns a 404 if the rating doesn't exist. Returns a 403 if the user is trying to delete someone else's rating and is not staff. Staff can delete any rating
    """
    db_rating = crud.get_rating_pointer(db, ratingID)
    if db_rating is None:
        raise HTTPException(status_code=404, detail="Rating not found")
    if user.accessLevel == accessLevel.ADMIN or db_rating.username == user.username:
        crud.delete_rating(db, ratingID)
    else:
        raise HTTPException(status_code=401, detail="Forbidden")


# =============================================================================== MODERATION


@app.get("/places/verification", response_model=List[schemas.GetPlace], tags=["Moderation"])
def list_unverified_places(skip: int = 0, limit: int = 100, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Gets a list of unverified places and their information

    - skip: will offset the places returned
    - limit: will return either this amount of places or the number of places after the skip offset, whichever is smaller
    """
    if user.accessLevel == accessLevel.USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    places = get_places_by_popularity(db, skip, limit, visibility.UNVERIFIED)
    return places

@app.post("/places/setverification", status_code=status.HTTP_200_OK, tags=["Moderation"])
def set_place_verified(isverified: bool, placeID: int, db: Session = Depends(get_db), user: schemas.InternalUser = Depends(get_current_user)):
    """
    Sets the visibility of a place:

    - isverified: boolean value of place visibility
    - placeID: the id to fetch. Will always be an integer

    Note: Only staff can use this command, otherwise it will respond with a 401. 
    """
    if user.accessLevel == accessLevel.USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    place = crud.get_place(db, placeID)
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    set_place_visibility(db, placeID, isverified)

@app.get("/images/verification", response_model=List[schemas.Thumbnail], tags=["Moderation"])
def list_unverified_images(skip: int = 0, limit: int = 100, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Gets a list of unverified images and their information

    - skip: will offset the images returned
    - limit: will return either this amount of images or the number of images after the skip offset, whichever is smaller
    """
    if user.accessLevel == accessLevel.USER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return get_unverified_thumbnails(db, skip, limit)

@app.post("/images/setverification", status_code=status.HTTP_200_OK, tags=["Moderation"])
def set_image_verified(isverified: bool, imageID: int, db: Session = Depends(get_db), user: schemas.InternalUser = Depends(get_current_user)):
    """
    Sets the visibility of an image:

    - isverified: boolean value of image visibility
    - placeID: the id to fetch. Will always be an integer

    Note: Only staff can use this command, otherwise it will respond with a 401. 
    """
    if user.accessLevel == accessLevel.USER:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    image = crud.get_thumbnail(db, imageID)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    crud.set_thumbnail_visibility(db, imageID, isverified)


# =============================================================================== SECURITY

@app.post("/login", tags=["Security"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Generates a user ACCOUNT token.

    - Requires OAuth2 form data to be sent

    Note: Returns a 400 if either the email or password are incorrect.
    """
    user = crud.get_user(db, form_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    if user.verified == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has not been verified")
    hashed_password = crud.hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    access_token = create_token(db, email=form_data.username, type=tokenType.ACCOUNT)

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/refreshToken", response_model=schemas.InternalUser, tags=["Security"])
async def refresh_token(user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Attempts to refresh the logged in user's token

    - Tokens expire 15 minutes after they've either been issued initially or refreshed with this endpoint

    Note: Returns a 400 if the token has expired. Requires reauthentication.
    """
    if not crud.refresh_token_by_user(db, user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")

@app.post("/verifyAccount", status_code=status.HTTP_200_OK, tags=["Security"])
async def verify_token(token: schemas.Token, db: Session = Depends(get_db)):
    """
    Attempts to verify a user account given a VERIFICATION type token

    - VERIFICATION tokens never expire

    Note: Returns a 400 if the token is invalid.
    """
    token_obj = crud.get_token_by_token(db, token.token)
    if not token and not token_obj.type == tokenType.VERIFICATION:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")
    verify_account(db, token.token)

@app.post("/resentVerificationEmail", status_code=status.HTTP_200_OK, tags=["Security"])
async def verify_email(email: str, db: Session = Depends(get_db)):
    """
    Resends verification email

    - email: email to resend to

    Note: Returns a 404 if the email has no associated token.
    """
    user = crud.get_user_from_username(db, email)
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that email does not exist")

    token = crud.get_token_by_user(db, user.username, tokenType.VERIFICATION)

    if token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")

    send_verification_email(user, token)

@app.post("/forgotpassword", status_code=status.HTTP_200_OK, tags=["Security"])
async def forgot_password(email: str, request: Request, db: Session = Depends(get_db)):
    """
    Sends an email containing a token to reset an account password

    - email: email to resend to

    Note: Returns a 404 if the email has no associated token.
    """
    user = crud.get_user(db, email)
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with that email does not exist")

    token = crud.get_token_by_user(db, user.email, tokenType.PASSRESET)
    if token is not None:
        db.delete(token)
        db.commit()

    token = crud.create_token(db, user.email, tokenType.PASSRESET)
    requesting_ip = request.client.host
    send_reset_email(user, token, requesting_ip)

@app.get("/resetpassword", status_code=status.HTTP_200_OK, tags=["Security"])
async def verify_token(token: str, new_password: str, db: Session = Depends(get_db)):
    """
    Attempts to reset a user account password given a PASSRESET type token

    - PASSRESET tokens expire after 24 hours

    Note: Returns a 400 if the token is invalid.
    """
    token_obj = crud.get_token_by_token(db, token)
    if token_obj is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")
    elif token_obj.expires < datetime.now() or not token_obj.type == tokenType.PASSRESET:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad token")
    reset_password(db, new_password, token)
    db.delete(get_token_by_user(db, token_obj.email, tokenType.ACCOUNT))
    db.delete(token_obj)
    db.commit
# =============================================================================== DEBUG

@app.get("/", tags=["Debug"], deprecated=True)
async def debug():
    """
    Used for development to test functionality that requires an endpoint. Non functional
    """
    import ipinfo

    from secret_config import IPINFO_ACCESS_TOKEN
    ip = "134.53.116.212"
    handler = ipinfo.getHandler(IPINFO_ACCESS_TOKEN)
    response = handler.getDetails(ip).all
    
    return response
