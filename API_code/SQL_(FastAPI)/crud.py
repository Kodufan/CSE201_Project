from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import status, HTTPException
import models, schemas
from schemas import accessLevel


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def delete_user(db: Session, username: str):
    db.delete(get_user(db, username=username))
    db.commit()


# TODO: Implement hashing
def hash_password(password: str):
    return password


def create_user(db: Session, user: schemas.CreateUser):
    
    fake_hashed_password = hash_password(user.rawPassword)
    

    if get_user(db, user.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is taken")

    db_user = models.User(
        username=user.username, 
        hashed_password=fake_hashed_password, 
        accessLevel=accessLevel.USER, 
        accountCreated=datetime.now()  
    )

    db.add(db_user)
    db.commit()
        
    db.refresh(db_user)
    return db_user


def set_user_perms(db: Session, username: str, accessLevel: accessLevel):
    db_user = get_user(db, username=username)

    if db_user is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    db_user.accessLevel = accessLevel
    db.commit()
    db.refresh(db_user)
    return db_user


def get_places(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Place).offset(skip).limit(limit).all()

def create_place(db: Session, place: schemas.SetPlace, user: schemas.User):
    isStaff = user.accessLevel != accessLevel.USER
    
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
    return db.query(models.Place).filter(models.Place.placeID == placeID).first()


def get_places(db: Session, skip: int = 0, limit: int = 100):
    #TODO: Implement ability to get places by a certain location
    return db.query(models.Place).offset(skip).limit(limit).order_by('rating')


def delete_place(db: Session, placeID: int):
    db.delete(get_place(db, placeID=placeID))
    db.commit()