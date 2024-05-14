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
    email = userData.email
    password = userData.password

    try:
        user = auth.sign_in_with_email_and_password(
            email= email,
            password = password
        )

        print("User: ",user)

        getUserData = db.child("users").child(user["localId"]).get().val()
        getUserName= dict(getUserData)["name"]

        getUserId = dict(getUserData)["user_id"]

        print(getUserName)
        print(getUserId)
        

        userRole = 2

        if getUserName == "admin" and getUserId == 1:
            userRole = os.getenv("ADMIN_ROLE")

            jwtEncode = encode_jwt(user["localId"], user["email"], userRole , user["idToken"])
            print("admin login")

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
    id_number = userData.id_number
    name = userData.name
    floor = userData.floor
    email = userData.email
    password = userData.password
    profile_pict_url = userData.profile_pict_url

    try:
        user = auth.create_user_with_email_and_password(
            email = email,
            password = password
        )

        data = {
            "user_id": id_number,
            "name": name,
            "floor": floor,
            "email": email,
            "profile_pict_url": profile_pict_url,
            }
        
        insertData = db.child("users").child(user["localId"]).set(data)

        return JSONResponse(
            {"message": f"User with id number {id_number} successfully added!"},
            status_code = 201
            )
    
    except HTTPError:
        raise HTTPException(
            status_code = 401,
            detail = f"User with id number {id_number} already existed!"
        )
