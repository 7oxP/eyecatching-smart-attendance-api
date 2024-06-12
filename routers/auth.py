from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from requests.exceptions import HTTPError
from schemas.pydantic_schema import loginSchema, addUserSchema, validate_login_form, validate_add_user_form
import pyrebase
from config.firebase_config import firebase_config
from auth.jwt_handler import encode_jwt
from constants.operation_status import operationStatus
from services.upload_file_service import upload_profile_picture
from auth.jwt_bearer import JWTBearer
from auth.jwt_handler import decode_jwt
import json
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
async def login(userData: loginSchema = Depends(validate_login_form)):
    email = userData.email
    password = userData.password

    try:
        user = auth.sign_in_with_email_and_password(
            email= email,
            password = password
        )

        userData = db.child("users").child(user["localId"]).get().val()
        userRole = dict(userData)["role"]
        
        jwtEncode = encode_jwt(user["localId"], user["email"], userRole , user["idToken"])

        data = dict(userData)

        return JSONResponse(
            {
            "message": "Successfully login!",
            "operation_status": operationStatus.get("success"),
            "data": {
                "user": data
            },
            "token": jwtEncode
            }, 
            status_code = 200
                )
    
    except HTTPError:
        return JSONResponse(
            {
            "message":"Failed to login, username or password is invalid!",
            "operation_status": operationStatus.get("authInvalidCredential"),
            },
            status_code = 401
            )

@router.post("/users", tags=["Auth"])
async def add_user(userData: addUserSchema = Depends(validate_add_user_form), image_file: UploadFile = File(...), authorization: str = Depends(JWTBearer())):
    id_number = userData.id_number
    name = userData.name
    floor = userData.floor
    email = userData.email
    password = userData.password
    userRole = 2

    try:
        jwtPayload = decode_jwt(authorization)
        userRole = jwtPayload["role"]
        adminRole = os.getenv("ADMIN_ROLE")

        if userRole != int(adminRole):
            return JSONResponse(
                {
                    "message": "User unauthorized",
                    "operation_status": operationStatus.get("unauthorizedAccess"),
                },
                status_code=401
            )
        
        existingUser = db.child("users").order_by_child("user_id").equal_to(id_number).get().val()

        if existingUser:
            return JSONResponse(
            {
                "message": f"User with id {id_number} already exists!",
                "operation_status": operationStatus.get("repoError"),

            },
            status_code = 409
            )
        
        user = auth.create_user_with_email_and_password(
            email = email,
            password = password
        )

        uploadProfilePict = await upload_profile_picture(image_file, authorization)
        uploadedProfilePictURL = uploadProfilePict.body
        uploadedProfilePictURL = json.loads(uploadedProfilePictURL)

        profilePictURL = uploadedProfilePictURL["profile_picture_url"]

        data = {
            "user_id": id_number,
            "name": name,
            "floor": floor,
            "email": email,
            "profile_pict_url": profilePictURL,
            "role": userRole,
            }
        
        insertData = db.child("users").child(user["localId"]).set(data)

        return JSONResponse(
            {
                "message": f"User with id number {id_number} successfully added!",
                "operation_status": operationStatus.get("success"),
                "data":{
                    "user": data
                }
            },
            status_code = 201
            )
    
    except HTTPError:
        return JSONResponse(
        {
            "message": "Email already exists!",
            "operation_status": operationStatus.get("repoError"),

        },
        status_code = 409
        )
