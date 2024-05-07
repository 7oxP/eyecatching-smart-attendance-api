from fastapi import FastAPI, File, UploadFile
import firebase_admin
from firebase_admin import credentials, storage
import pyrebase
from models import addUserSchema, loginSchema, updateUserSchema
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from requests.exceptions import HTTPError
from PIL import Image
from io import BytesIO
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

cred = credentials.Certificate("serviceAccountKey.json")

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


@app.post("/addUser")
async def addUser(userData: addUserSchema):
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
        

@app.post("/login")
async def login(userData: loginSchema):
    username = userData.username
    password = userData.password

    try:
        user = auth.sign_in_with_email_and_password(
            email=f"{username}@mail.com",
            password = password
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
    

@app.post("/uploadProfilePict")
async def uploadProfilePict(profilePict: UploadFile = File(...)):

    contents = await profilePict.read()
    
    image = Image.open(BytesIO(contents))
    
    img_io = BytesIO()
    image.save(img_io, format="JPEG")
    img_io.seek(0)
    
    blob = bucket.blob("profile_pictures/" + profilePict.filename)
    blob.upload_from_file(img_io, content_type='image/jpeg')
    
    return JSONResponse(
        {
            "message": "Image successfully uploaded!"}, 
            status_code=200
        )


@app.put("/updateUser/{userId}")
async def updateUser(userData: updateUserSchema):
    pass

@app.get("/getUser/{userId}")
async def getUser():
    pass

@app.get("/getUserGalleryLogs/{userId}")
async def getUserGalleryLogs():
    pass

@app.get("/getUserAttendanceLogs/{userId}")
async def getUserAttendanceLogs():
    pass

@app.get("/getAttendanceStatus/{userId}")
async def getUserAttendanceStatus():
    pass
