from fastapi import APIRouter, File, UploadFile, Depends, Path, Form
from fastapi.responses import JSONResponse
from PIL import Image
from io import BytesIO
from schemas.pydantic_schema import updateUserSchema
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

    contents = await profile_pict.read()
    
    image = Image.open(BytesIO(contents))
    
    img_io = BytesIO()
    image.save(img_io, format="JPEG")
    img_io.seek(0)

    extractJWTPayload = decode_jwt(authorization)
    
    getUserId = extractJWTPayload["user_id"]
    getUserIdToken = extractJWTPayload["user_id_token"]

    uploadProfilePicture = storage.child("profile_pictures/" + profile_pict.filename).put(file=img_io, token=getUserIdToken, content_type='image/jpeg')

    getProfilePictureURL = storage.child("profile_pictures/" + profile_pict.filename).get_url(getUserIdToken)

    updateProfilePictURL = db.child("users").child(getUserId).update({"profile_pict_url":getProfilePictureURL})

    return JSONResponse(
        {
            "message": "Image successfully uploaded!",
            "profile_picture_url": getProfilePictureURL,
        },
            status_code=200
        )


@router.get("/users/attendance-logs")
async def get_user_attendance_logs(authorization: str = Depends(JWTBearer())):

    extractJWTPayload = decode_jwt(authorization)

    getUserId = extractJWTPayload["user_id"]

    getChildNode = db.child("users_attendance_logs").child(getUserId).shallow().get().val()

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
            {"message": f"data successfully added!"},
            status_code = 201
            )
    
    except Exception as e:
        # raise HTTPException(
        #     status_code = 401,
        #     detail = f"failed to add data!"
        # )
        print(e)


@router.get("/users/{user_id}/gallery-logs")
async def get_user_gallery_logs():
    pass

@router.get("/users/{user_id}/attendance-status")
async def get_user_attendance_status():
    pass

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int = Path(...)):
    user = user_id
    print(user)
    return (user)

@router.put("/users/{user_id}")
async def update_user(userData: updateUserSchema):
    pass


@router.get("/users")
async def get_all_users(authorization: str = Depends(JWTBearer())):
    extractJWTPayload = decode_jwt(authorization)
    getUserRole = extractJWTPayload["role"]

    if getUserRole != os.getenv("ADMIN_ROLE"):
        return JSONResponse(
            {
                "message": "User unauthorized",
            },
            status_code=401
        )
    
