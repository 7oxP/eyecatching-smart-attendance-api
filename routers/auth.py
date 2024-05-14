from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from requests.exceptions import HTTPError
from schemas.pydantic_schema import loginSchema, addUserSchema
import pyrebase
from config.firebase_config import firebase_config
from auth.jwt_handler import encode_jwt
import os
from dotenv import load_dotenv

load_dotenv()


firebase = pyrebase.initialize_app(firebase_config())
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()


router = APIRouter(
    prefix="/api",
    tags=["Auth"],
    )


@router.post("/login", tags=["Auth"])
async def login(userData: loginSchema):
    username = userData.username
    password = userData.password

    try:
        user = auth.sign_in_with_email_and_password(
            email=f"{username}@mail.com",
            password = password
        )

        print("User: ",user)

        userRole = 2

        if username == "admin":
            userRole = os.getenv("ADMIN_ROLE")

            jwtEncode = encode_jwt(user["localId"], user["email"], userRole , user["idToken"])

            return JSONResponse(
                {
                "message": "Successfully login!",
                "token": jwtEncode
                }, 
                status_code = 200
                )
        
        jwtEncode = encode_jwt(user["localId"], user["email"], userRole , user["idToken"])

        return JSONResponse(
            {
            "message": "Successfully login!",
            "token": jwtEncode
            }, 
            status_code = 200
                )

    
    except:
        raise HTTPException(
            status_code = 401,
            detail = "Failed to login, username or password is invalid!"
            )
    


@router.post("/users", tags=["Auth"])
async def add_user(userData: addUserSchema):
    name = userData.name
    position = userData.position 
    floor = userData.floor
    username = userData.username
    password = userData.password

    try:
        user = auth.create_user_with_email_and_password(
            email = f"{username}@mail.com",
            password = password
        )

        data = {
            "user_id": user["localId"],
            "name":name,
            "position":position,
            "floor":floor,
            "profile_pict_url": "-"
            }
        
        insertData = db.child("users").child(user["localId"]).set(data)

        print(user)
        print(insertData)

        return JSONResponse(
            {"message": f"User named {username} successfully added!"},
            status_code = 201
            )
    
    except HTTPError:
        raise HTTPException(
            status_code = 401,
            detail = f"User {username} already existed!"
        )
