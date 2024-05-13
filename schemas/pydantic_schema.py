from pydantic import BaseModel

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

class addAttendanceLogs(BaseModel):
    status: str
