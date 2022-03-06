import crud
from shutil import copyfileobj
from fastapi import Depends, UploadFile, HTTPException, status
from pathlib2 import PurePosixPath
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List
from config import ACCEPTABLE_FILE_EXTENSIONS
from database import SessionLocal
from schemas import InternalUser


# Gets database instance
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def write_file(filePath: Path, file: UploadFile):
    if not filePath.exists():
        filePath.mkdir()

    with open(filePath / file.filename, "wb+") as file_object:
        copyfileobj(file.file, file_object)
    return file.filename

async def write_files(filePath: Path, files: List[UploadFile], existing_urls: List[str]):
    urls = list()

    for file in files:
        if PurePosixPath(file.filename).suffix not in ACCEPTABLE_FILE_EXTENSIONS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File(s) contain unacceptable type")
    for file in files:
        file_name = ''

        while True:
            file_name = crud.make_random_string(10)
            if file_name not in existing_urls:
                break
        file.filename = file_name + PurePosixPath(file.filename).suffix
        urls.append(await write_file(filePath, file))
    return urls

def decode_token(db, token: str):
    return crud.get_user_from_token(db, token)

def send_verification_email(db: Session, user: InternalUser):
    return