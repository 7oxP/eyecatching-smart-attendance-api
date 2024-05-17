from fastapi import File, UploadFile, Depends
from fastapi.responses import JSONResponse
import pyrebase
from auth.jwt_bearer import JWTBearer
from auth.jwt_handler import decode_jwt
from PIL import Image
from io import BytesIO
from config.firebase_config import firebase_config
import uuid

firebase = pyrebase.initialize_app(firebase_config())
db = firebase.database()
storage = firebase.storage()

async def upload_profile_picture(image_file: UploadFile = File(...), authorization: str = Depends(JWTBearer())):

    try:
        contents = await image_file.read()
        
        image = Image.open(BytesIO(contents))
        
        img_io = BytesIO()
        image.save(img_io, format="JPEG")
        img_io.seek(0)

        extractJWTPayload = decode_jwt(authorization)
        
        getUserId = extractJWTPayload["user_id"]
        getUserIdToken = extractJWTPayload["user_id_token"]

        uploadProfilePicture = storage.child("profile_pictures/" + image_file.filename).put(file=img_io, token=getUserIdToken, content_type='image/jpeg')

        getProfilePictureURL = storage.child("profile_pictures/" + image_file.filename).get_url(getUserIdToken)

        updateProfilePictURL = db.child("users").child(getUserId).update({"profile_pict_url":getProfilePictureURL})

        return JSONResponse(
            {
                "message": "Image successfully uploaded!",
                "profile_picture_url": getProfilePictureURL,
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

async def upload_captured_image(image_file: UploadFile = File(...), folder_path: str = None, user_id: int = None, user_base_node: str = None):
    contents = await image_file.read()
    
    image = Image.open(BytesIO(contents))
    
    img_io = BytesIO()
    image.save(img_io, format="JPEG")
    img_io.seek(0)

    uploadImage = storage.child(folder_path + image_file.filename).put(file=img_io, content_type='image/jpeg')

    getImageURL = storage.child(folder_path + image_file.filename).get_url(uuid.uuid1())

    return JSONResponse(
        {
            "message": "Image successfully uploaded!",
            "image_url": getImageURL
        },
            status_code=200
        )

