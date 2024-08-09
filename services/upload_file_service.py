from fastapi import File, UploadFile, Depends
from fastapi.responses import JSONResponse
import pyrebase
from auth.jwt_bearer import JWTBearer
from auth.jwt_handler import decode_jwt
from PIL import Image
from io import BytesIO
from config.firebase_config import firebase_config
import uuid
from constants.operation_status import operationStatus
from datetime import datetime
from zoneinfo import ZoneInfo

firebase = pyrebase.initialize_app(firebase_config())
db = firebase.database()
storage = firebase.storage()

async def upload_profile_picture(userId: int, image_file: UploadFile = File(...), authorization: str = Depends(JWTBearer())):

    try:
        if image_file is None:
            return JSONResponse(
                {
                    "message": "Please provide image file to be uploaded!",
                    "operation_status": operationStatus.get("fieldValidationError")
                },
                status_code=422
            )
        
        contents = await image_file.read()

        
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        img_io = BytesIO()
        image.save(img_io, format="JPEG")
        img_io.seek(0)

        jwtPayload = decode_jwt(authorization)
        
        nodesName = jwtPayload["user_id"]
        userIdToken = jwtPayload["user_id_token"]

        uploadProfilePicture = storage.child(f"profile_pictures/{userId}_profile_picture.jpg").put(file=img_io, token=userIdToken, content_type='image/jpeg')

        getProfilePictureURL = storage.child(f"profile_pictures/{userId}_profile_picture.jpg").get_url(userIdToken)

        updateProfilePictURL = db.child("users").child(nodesName).update({"profile_pict_url":getProfilePictureURL})

        return JSONResponse(
            {
                "message": "Image successfully uploaded!",
                "profile_picture_url": getProfilePictureURL,
                "operation_status": operationStatus.get("success"),
            },
                status_code=200
            )
   
    except Exception as err:
        return JSONResponse(
            {
                "message": str(err)
            },
                status_code=500
            )

async def upload_captured_image(image_file: UploadFile = File(...), user_id: int = None):
    
    # try:
        if image_file is None:
            return JSONResponse(
                {
                    "message": "Please provide image file to be uploaded!",
                    "operation_status": operationStatus.get("fieldValidationError")
                },
                status_code=422
            )

        contents = await image_file.read()
        
        image = Image.open(BytesIO(contents)).convert("RGB")
        
        img_io = BytesIO()
        image.save(img_io, format="JPEG")
        img_io.seek(0)

        timestamp = datetime.now(ZoneInfo('Asia/Jakarta'))
        timestamp = timestamp.strftime("%Y-%m-%d_%H:%M")


        uploadImage = storage.child("captured_images/notification_" + str(user_id) + "_" + timestamp).put(file=img_io, content_type='image/jpeg')

        getImageURL = storage.child("captured_images/notification_" + str(user_id) + "_"  + timestamp).get_url(uuid.uuid1())

        return JSONResponse(
            {
                "message": "Image successfully uploaded!",
                "image_url": getImageURL,
                "operation_status": operationStatus.get("success")
            },
                status_code=200
            )

    # except Exception as err:
    #     return JSONResponse(
    #         {
    #             "message": str(err)
    #         },
    #             status_code=500
    #         )
