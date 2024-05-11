from fastapi import FastAPI, File, UploadFile, Depends, Header
import firebase_admin
from firebase_admin import credentials, storage
import pyrebase
from models import addUserSchema, loginSchema, updateUserSchema, addAttendanceLogs
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from requests.exceptions import HTTPError
from PIL import Image
from io import BytesIO
from jose import JWTError, jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from auth.jwt_handler import encode_jwt, decode_jwt
from auth.jwt_bearer import JWTBearer
import os


load_dotenv()


firebaseConfig = {
  "apiKey": "AIzaSyAHnhBpwvVKWXWx1JVKHTrSpJgd0OnR6YA",
  "authDomain": "smart-attendance-da7f6.firebaseapp.com",
  "projectId": "smart-attendance-da7f6",
  "storageBucket": "smart-attendance-da7f6.appspot.com",
  "messagingSenderId": "382545441680",
  "appId": "1:382545441680:web:b704e8b2d8024aa61fb915",
  "measurementId": "G-0316NWF9NF",
  "databaseURL": "https://smart-attendance-da7f6-default-rtdb.asia-southeast1.firebasedatabase.app"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

app = FastAPI(docs_url="/")


@app.post("/users", tags=["Auth"])
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
        

@app.post("/login", tags=["Auth"])
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
    

@app.post("/users/profile-picture", tags=["User"])
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


@app.put("/users/{user_id}", tags=["User"])
async def update_user(userData: updateUserSchema):
    pass


@app.get("/users", tags=["User"])
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
    

@app.get("/users/{user_id}", tags=["User"])
async def get_user_by_id():
    pass

@app.get("/users/{user_id}/gallery-logs", tags=["User"])
async def get_user_gallery_logs():
    pass

@app.get("/users/attendance-logs", tags=["User"])
async def get_user_attendance_logs(user_id: str, authorization: str = Depends(JWTBearer())):

    extractJWTPayload = decode_jwt(authorization)

    getUserId = extractJWTPayload["user_id"]

    data = db.child("users_attendance_logs").child(getUserId).get()

    return JSONResponse(
            {"message": "ok", 
             "data": data.val()
             },
            status_code = 201
            )

@app.get("/users/{user_id}/attendance-status", tags=["User"])
async def get_user_attendance_status():
    pass

@app.post("/users/attendance-logs")
async def insert_user_attendance_logs(userData: addAttendanceLogs, authorization: str = Depends(JWTBearer())):

    try:
        extractJWTPayload = decode_jwt(authorization)
        getUserId = extractJWTPayload["user_id"]


        status = userData.status
        timestamp = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M")
        capturedFace = None


        data = {
            "status":status,
            "timestamp":timestamp,
            "captured_face":capturedFace,
        }

        getTotalNodes = db.child("users_attendance_logs").child(getUserId).shallow().get().val()
        totalNodes = None

        try:
            totalNodes = sorted(getTotalNodes)[-1].split("_")[-1]
            totalNodes = int(totalNodes)        
        except:
            totalNodes = 0
        
        insertData = db.child("users_attendance_logs").child(getUserId).child(f"attendance_{totalNodes+1}").set(data)

        # print(insertData)

        return JSONResponse(
            {"message": f"data successfully added!"},
            status_code = 201
            )
    
    except HTTPError:
        raise HTTPException(
            status_code = 401,
            detail = f"failed to add data!"
        )

@app.get("/employee", dependencies=[Depends(JWTBearer())])
async def get_employee_list():
        pass
