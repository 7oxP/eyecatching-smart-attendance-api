from pydantic import BaseModel
from fastapi import File, UploadFile

class addUserSchema(BaseModel):
    name: str
    position: str
    floor: str
    # start_time: str
    # end_time: str
    username: str
    password: str

class loginSchema(BaseModel):
    username: str
    password: str

class updateUserSchema(BaseModel):
    name: str
    position: str
    floor: str
    # start_time: str
    # end_time: str
    username: str
    password: str
    profilePict: bytes

