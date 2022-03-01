from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import status, HTTPException
import models, schemas
from schemas import accessLevel


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def delete_user(db: Session, username: str):
    db.delete(get_user(db, username=username))
    db.commit()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

# TODO: Implement hashing
def hash_password(password: str):
    return password


def create_user(db: Session, user: schemas.CreateUser):
    
    fake_hashed_password = hash_password(user.rawPassword)
    

    if get_user(db, user.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is taken")

    db_user = models.User(username=user.username, hashed_password=fake_hashed_password, accessLevel=accessLevel.USER, accountCreated=datetime.now())
    db.add(db_user)
    db.commit()
        
    db.refresh(db_user)
    return db_user


def set_user_perms(db: Session, username: str, accessLevel: accessLevel):
    db_user = get_user(db, username=username)
    db_user.accessLevel = accessLevel
    db.commit()
    db.refresh(db_user)
    return db_user


def get_places(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Place).offset(skip).limit(limit).all()