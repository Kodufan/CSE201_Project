from sqlite3 import OperationalError
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc

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

@app.post("/createUser", response_model=User, status_code=201)
def create_user(user: CreateUser, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.post("/setUserPerms", response_model=User, status_code=200)
def set_perms(username: str, accessLevel: accessLevel, db: Session = Depends(get_db)):
    return set_user_perms(db, username, accessLevel)

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{username}", status_code=200)
def delete_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    crud.delete_user(db, username=username)