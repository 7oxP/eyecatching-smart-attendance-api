from fastapi import APIRouter, File, UploadFile, Depends, Path, Form
from fastapi.responses import JSONResponse
from schemas.pydantic_schema import updateUserSchema, validate_update_user_form
import pyrebase
from config.firebase_config import firebase_config
from auth.jwt_handler import decode_jwt
from auth.jwt_bearer import JWTBearer
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv
from services.upload_file_service import upload_profile_picture, upload_captured_image
import json

load_dotenv()

firebase = pyrebase.initialize_app(firebase_config())
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()


router = APIRouter(
    prefix="/api",
    tags=["Users"],
    )


@router.post("/users/profile-picture")
async def upload_profile_pict(profile_pict: UploadFile = File(...), authorization: str = Depends(JWTBearer())):
    uploadProfilePict = await upload_profile_picture(profile_pict, authorization)

    return uploadProfilePict


@router.get("/users/attendance-logs")
async def get_user_attendance_logs(authorization: str = Depends(JWTBearer())):

    try:
        extractJWTPayload = decode_jwt(authorization)

        getUserId = extractJWTPayload["user_id"]

        getChildNode = db.child("users_attendance_logs").child(getUserId).shallow().get().val()

        if getChildNode is None:
            return JSONResponse(
            {
            "message": "User does not have any attendance logs",
            "data": None,
            }, status_code=200
            )

        dataAttendance = {}
        print(list(getChildNode))

        for childNode in list(getChildNode):
            print(childNode)
            getAttendances = db.child("users_attendance_logs").child(getUserId).child(childNode).get().val()
            
            dataAttendance[childNode] = dict(getAttendances)
        
        print("data attendance:",dataAttendance)

        return JSONResponse(
            {"message": "ok",
            "data": dataAttendance,
            }, status_code=200
            )
    
    except Exception as err:
        return JSONResponse(
            {"message": str(err),
            "data": None,
            }, status_code=500
            )


@router.post("/users/attendance-logs")
async def insert_user_attendance_logs(user_id: int = Form(...), floor: str = Form(...), status: str = Form(...), image_file: UploadFile = File(...)):

    try:
        getNodesName = db.child("users").order_by_child("user_id").equal_to(user_id).get().val()
        getNodesName = next(iter(getNodesName))

        floor = floor
        status = status
        timestamp = datetime.now(ZoneInfo('Asia/Jakarta'))
        captured_image = image_file

        getAttendanceTime = db.child("users_attendance_logs").child(getNodesName).child(timestamp.strftime("%Y-%m-%d")).get().val()

        if getAttendanceTime:
            return JSONResponse(
            {"message": f"User's already attended!"},
            status_code = 409
            )
        
        uploadCapturedImage = await upload_captured_image(captured_image, "captured_images/", user_id, getNodesName)
        getCapturedImageURL = uploadCapturedImage.body
        getCapturedImageURL = json.loads(getCapturedImageURL)

        capturedImageURL = getCapturedImageURL["image_url"]

        data = {
            "floor": floor,
            "status": status,
            "timestamp": timestamp.strftime("%a, %d %b %Y %H:%M"),
            "captured_face_url": capturedImageURL,
        }
                
        insertData = db.child("users_attendance_logs").child(getNodesName).child(timestamp.strftime("%Y-%m-%d")).set(data)


        return JSONResponse(
            {"message": f"data successfully added!",
             "data": data
             },
            status_code = 201
            )
    
    except Exception as err:
        return JSONResponse(
            {"message": str(err),
            "data": None,
            }, status_code=500
            )

@router.get("/users/{user_id}/gallery-logs")
async def get_user_gallery_logs():
    pass

@router.get("/users/attendance-status")
async def get_user_attendance_status(authorization: str = Depends(JWTBearer())):
    try:
        timestamp = datetime.now(ZoneInfo('Asia/Jakarta'))
        currentDate = timestamp.strftime("%Y-%m-%d")

        extractJWTPayload = decode_jwt(authorization)

        getUserId = extractJWTPayload["user_id"]

        getChildNode = db.child("users_attendance_logs").child(getUserId).shallow().get().val()

        getUserLastAttendanceDate = list(getChildNode)[-1]
        
        if getUserLastAttendanceDate != currentDate:
            return JSONResponse(
            {"message": "the user has not checked in yet",
            "attendance_status": "absent",
            }, status_code=200
            )
        
        return JSONResponse(
            {"message": "the user has checked in",
            "attendance_status": "present",
            }, status_code=200
            )
        
    except Exception as err:
        return JSONResponse(
            {"message": str(err),
            "data": None,
            }, status_code=200
            )
    pass

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int = Path(...)):
    user = user_id
    print(user)
    return (user)

@router.put("/users/{user_id}")
async def update_user(userData: updateUserSchema = Depends(validate_update_user_form)):
    pass


@router.get("/users")
async def get_all_users(authorization: str = Depends(JWTBearer())):
    extractJWTPayload = decode_jwt(authorization)
    getUserRole = extractJWTPayload["role"]
    adminRole = os.getenv("ADMIN_ROLE")

    if getUserRole != int(adminRole):
        return JSONResponse(
            {
                "message": "User unauthorized",
            },
            status_code=401
        )
    
    getUsers = db.child("users").get().val()
    
    return JSONResponse({"message":"success",
                         "data":getUsers
                         }, 
                         status_code=200)
    
