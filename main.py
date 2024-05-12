from fastapi import FastAPI, APIRouter, File, UploadFile, Depends, Path
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
  "apiKey": os.getenv("API_KEY"),
  "authDomain": os.getenv("AUTH_DOMAIN"),
  "projectId": os.getenv("PROJECT_ID"),
  "storageBucket": os.getenv("STORAGE_BUCKET"),
  "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
  "appId": os.getenv("APP_ID"),
  "measurementId": os.getenv("MEASUREMENT_ID"),
  "databaseURL": os.getenv("DATABASE_URL"),
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

app = FastAPI(docs_url="/")
router = APIRouter()


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


# @app.put("/users/{user_id}", tags=["User"])
# async def update_user(userData: updateUserSchema):
#     pass


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
    

@app.get("/users/attendance-logs", tags=["User"])
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


@app.post("/users/attendance-logs", tags=["User"])
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
    
@app.get("/users/{user_id}", tags=["User"])
async def get_user_by_id(user_id: int = Path(...)):
    user = user_id
    print(user)
    return (user)

@app.get("/users/{user_id}/gallery-logs", tags=["User"])
async def get_user_gallery_logs():
    pass

@app.get("/users/{user_id}/attendance-status", tags=["User"])
async def get_user_attendance_status():
    pass
