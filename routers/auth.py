from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from requests.exceptions import HTTPError
from schemas.pydantic_schema import loginSchema, addUserSchema, validate_login_form, validate_add_user_form
import pyrebase
from config.firebase_config import firebase_config
from auth.jwt_handler import encode_jwt
import json

firebase = pyrebase.initialize_app(firebase_config())
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()


router = APIRouter(
    prefix="/api",
    tags=["Auth"],
    )


@router.post("/login", tags=["Auth"])
async def login(userData: loginSchema = Depends(validate_login_form)):
    email = userData.email
    password = userData.password

    try:
        user = auth.sign_in_with_email_and_password(
            email= email,
            password = password
        )

        getUserData = db.child("users").child(user["localId"]).get().val()
        getUserName= dict(getUserData)["name"]

        getUserRole = dict(getUserData)["user_role"]
        
        jwtEncode = encode_jwt(user["localId"], user["email"], getUserRole , user["idToken"])

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
async def add_user(userData: addUserSchema = Depends(validate_add_user_form)):
    id_number = userData.id_number
    name = userData.name
    floor = userData.floor
    email = userData.email
    password = userData.password
    profile_pict_url = userData.profile_pict_url
    userRole = 2

    try:
        getExistingUser = db.child("users").order_by_child("user_id").equal_to(id_number).get().val()

        if getExistingUser:
            return JSONResponse(
            {
                "message": f"User with id {id_number} already exists!"
            },
            status_code = 409
            )
        
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
            "role": userRole,
            }
        
        insertData = db.child("users").child(user["localId"]).set(data)

        return JSONResponse(
            {
                "message": f"User with id number {id_number} successfully added!"
            },
            status_code = 201
            )
    
    except HTTPError:
        return JSONResponse(
        {
            "message": "Email already exists!"
        },
        status_code = 409
        )
