from pydantic import BaseModel, EmailStr, ValidationError
from fastapi import Form, HTTPException
from typing import Optional

class addUserSchema(BaseModel):
    id_number: int
    name: str
    floor: int
    # start_time: str
    # end_time: str
    email: EmailStr
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

def validate_add_user_form(  
                            id_number: int = Form(...),
                            name: str = Form(...),
                            floor: int = Form(...),
                            email: str = Form(...),
                            password: str = Form(...),
                            profile_pict_url: str = Form(...),
                          ) -> addUserSchema:
    try:
        return addUserSchema(id_number=id_number, name=name, floor=floor, email=email, password=password, profile_pict_url=profile_pict_url)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

class loginSchema(BaseModel):
    email: EmailStr
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

def validate_login_form(email: str = Form(...), password: str = Form(...)) -> loginSchema:
    try:
        return loginSchema(email=email, password=password)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

class updateUserSchema(BaseModel):
    name: Optional[str]
    floor: Optional[int]
    # start_time: str
    # end_time: str
    email: Optional[EmailStr]
    profile_pict_url: Optional[str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "XL User",
                    "floor": 20,
                    "email": "user@xl.com",
                    "profile_pict": "imageName.jpg"
                }
            ]
        }
    }

def validate_update_user_form(  
                            name: Optional[str] = Form(None),
                            floor: Optional[int] = Form(None),
                            email: Optional[EmailStr] = Form(None),
                            profile_pict_url: Optional[str] = Form(None),
                          ) -> updateUserSchema:
    try:
        return updateUserSchema(name=name, floor=floor, email=email, profile_pict_url=profile_pict_url)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
