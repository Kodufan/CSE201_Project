from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud
from crud import *
from database import SessionLocal, engine
from models import *
from schemas import *
from schemas import accessLevel, tokenType

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security

def decode_token(db, token: str):
    user = crud.get_user_from_token(db, token)
    if user is None:
        raise HTTPException(status_code=400, detail="Bad token")
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = decode_token(db, token)
    return user

# Endpoints

# =============================================================================== USERS


@app.post("/createUser", response_model=schemas.InternalUser, status_code=201)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.post("/setUserPerms", response_model=schemas.User, status_code=200)
def set_perms(username: str, accessLevel: accessLevel, db: Session = Depends(get_db), callingUser: schemas.InternalUser = Depends(get_current_user)):
    user = crud.get_user(db, username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Only sets perms if the logged in user is admin. Doesn't allow setting other users to admin. Doesn't allow demoting other admins including self
    if callingUser.accessLevel == accessLevel.ADMIN and not accessLevel == accessLevel.ADMIN and not user.accessLevel == accessLevel.ADMIN:
        set_user_perms(db, username, accessLevel)
    else:
        raise HTTPException(status_code=401, detail="Forbidden") 

@app.get("/users/", response_model=List[schemas.InternalUser])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users

@app.get("/user/{username}", response_model=schemas.InternalUser)
def get_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/user/", status_code=200)
def delete_user(user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=user.username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, username=user.username)


# =============================================================================== PLACES


@app.post("/createPlace", response_model=schemas.GetPlace, status_code=201)
def create_place(place: SetPlace, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_place(db, place, user)

@app.get("/place/{placeID}", response_model=schemas.GetPlace)
def get_place(placeID: int, db: Session = Depends(get_db)):
    db_place = crud.get_place(db, placeID=placeID)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return db_place

@app.get("/places/", response_model=List[schemas.GetPlace])
def list_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    places = get_places(db, skip=skip, limit=limit)
    return places

@app.delete("/place/{placeID}", status_code=200)
def delete_place(placeID: int, user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):

    if user.accessLevel == accessLevel.ADMIN:
        db_place = crud.get_place(db, placeID=placeID)
        if db_place is None:
            raise HTTPException(status_code=404, detail="Place not found")
        crud.delete_user(db, placeID=placeID)
    else:
        raise HTTPException(status_code=401, detail="Forbidden")


# =============================================================================== SECURITY


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user(db, form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    hashed_password = crud.hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_token(db, username=form_data.username, type=tokenType.ACCOUNT)

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/refreshToken", response_model=schemas.InternalUser)
async def login(user: schemas.InternalUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not crud.refresh_token_by_user(db, user):
        raise HTTPException(status_code=400, detail="Bad token")
