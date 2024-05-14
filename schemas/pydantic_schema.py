from pydantic import BaseModel

class addUserSchema(BaseModel):
    id_number: int
    name: str
    floor: int
    # start_time: str
    # end_time: str
    email: str
    password: str
    profile_pict_url: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id_number": 2107421069,
                    "name": "XL User",
                    "floor": 20,
                    "email": "user@xl.com",
                    "password": "p4ssw0rd",
                    "profile_pict_url": "https://profile-pict-url.com"
                }
            ]
        }
    }

class loginSchema(BaseModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@xl.com",
                    "password": "p4ssw0rd",
                }
            ]
        }
    }

class updateUserSchema(BaseModel):
    name: str
    position: str
    floor: int
    # start_time: str
    # end_time: str
    email: str
    password: str
    profile_pict: bytes

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "XL User",
                    "floor": 20,
                    "email": "user@xl.com",
                    "password": "p4ssw0rd",
                    "profile_pict": "uploadFile.jpg"
                }
            ]
        }
    }

class addAttendanceLogs(BaseModel):
    user_id: int
    status: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": 10,
                    "status": "presence",
                }
            ]
        }
    }
