from email.mime.text import MIMEText
import crud
from shutil import copyfileobj
from fastapi import Depends, UploadFile, HTTPException, status
from pathlib2 import PurePosixPath
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List
from config import ACCEPTABLE_FILE_EXTENSIONS, SERVER_IP
from database import SessionLocal
from schemas import InternalUser, tokenType
import smtplib, ssl
from secret_config import *


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

def send_verification_email(user: InternalUser, token: str):
    ssl_context = ssl.create_default_context()
    service = smtplib.SMTP_SSL(DOMAIN, PORT, context=ssl_context)
    service.login(EMAIL, PASSWORD)

    msg = f"""
Thanks for taking the first step in going on a trip to somewhere you've NeverBeen before!<br>
Please verify your account <a href="https://ceclnx01.cec.miamioh.edu/~duvalljc/index.html?token={token}">here</a><br><br>
Thanks,
NeverBeen."""
    msgMIME = MIMEText(msg,'html')
    result = service.sendmail(EMAIL, user.email, "Subject: Please verify your NeverBeen account!\n" + msgMIME.as_string())

    service.quit()
    return