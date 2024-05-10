from fastapi import FastAPI, File, UploadFile
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


load_dotenv()

cred = credentials.Certificate("service_accounts/serviceAccountKey.json")

firebase_admin.initialize_app(cred, {'storageBucket': 'smart-attendance-da7f6.appspot.com'})

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
# storage = firebase.storage()
bucket = storage.bucket()

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
            "profilePictURL": "-"
            }
        
        insertData = db.child("users").push(data)

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
            password = password, tags=["Auth"]
        )

        print("User: ",user)
        return JSONResponse(
            {
            "message": "Successfully login!"
            }, 
            status_code = 200
            )
    except:
        raise HTTPException(
            status_code = 401,
            detail = "Failed to login, username or password is invalid!"
            )
    

@app.post("/users/profile-picture", tags=["User"])
async def upload_profile_pict(profile_pict: UploadFile = File(...)):

    contents = await profile_pict.read()
    
    image = Image.open(BytesIO(contents))
    
    img_io = BytesIO()
    image.save(img_io, format="JPEG")
    img_io.seek(0)
    
    blob = bucket.blob("profile_pictures/" + profile_pict.filename)
    blob.upload_from_file(img_io, content_type='image/jpeg')
    
    return JSONResponse(
        {
            "message": "Image successfully uploaded!"}, 
            status_code=200
        )


@app.put("/users/{user_id}", tags=["User"])
async def update_user(userData: updateUserSchema):
    pass

@app.get("/users/{user_id}", tags=["User"])
async def get_user():
    pass

@app.get("/users/gallery-logs/{user_id}", tags=["User"])
async def get_user_gallery_logs():
    pass

@app.get("/users/attendance-logs/{user_id}", tags=["User"])
async def get_user_attendance_logs(user_id: int):
    data = db.child("users_attendance_logs").child(1).get()

    return JSONResponse(
            {"message": "ok", "data":data.val()},
            status_code = 201
            )

@app.get("/users/attendance-status/{user_id}", tags=["User"])
async def get_user_attendance_status():
    pass

@app.post("/users/attendance-logs/{user_id}")
async def insert_user_attendance_logs(userData: addAttendanceLogs):
    try:
        timestamp = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M")
        status = userData.status

        data = {
            "timestamp":timestamp,
            "status":status,
        }

        # for i in range(1, 10):
        #     insertData = db.child("users_attendance_logs").child(1).push(data)

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
