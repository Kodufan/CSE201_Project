from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import crud
from crud import *
from models import *
from schemas import *

from database import SessionLocal, engine
from schemas import accessLevel

models.Base.metadata.create_all(bind=engine)
app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/createUser", response_model=schemas.InternalUser, status_code=201)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.post("/setUserPerms", response_model=schemas.User, status_code=200)
def set_perms(username: str, accessLevel: accessLevel, db: Session = Depends(get_db)):
    return set_user_perms(db, username, accessLevel)

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

@app.delete("/user/{username}", status_code=200)
def delete_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, username=username)

@app.post("/createPlace", response_model=schemas.SetPlace, status_code=201)
def create_place(place: SetPlace, user: User, db: Session = Depends(get_db)):
    return crud.create_place(db, place, user)

@app.get("/place/{placeID}")
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
def delete_place(placeID: int, db: Session = Depends(get_db)):
    db_place = crud.get_place(db, placeID=placeID)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    crud.delete_user(db, placeID=placeID)