from fastapi import APIRouter, File, UploadFile, Depends, Path, Form
from fastapi.responses import JSONResponse
from schemas.pydantic_schema import updateUserSchema, validate_update_user_form
import pyrebase
import firebase_admin
from firebase_admin import credentials, auth, storage
from config.firebase_config import firebase_config
from auth.jwt_handler import decode_jwt
from auth.jwt_bearer import JWTBearer
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv
from services.upload_file_service import upload_profile_picture, upload_captured_image
from services.get_credentials_file import get_credentials
from services.notification_service import send_notification
import json
from constants.operation_status import operationStatus

load_dotenv()

storageBucket = os.getenv("STORAGE_BUCKET")
credentialsJSON = os.getenv("CREDENTIALS_JSON")

firebase = pyrebase.initialize_app(firebase_config())
db = firebase.database()

credentialsFile = get_credentials()

cred = credentials.Certificate(credentialsJSON)
firebase_admin.initialize_app(cred, {'storageBucket': storageBucket})

bucket = storage.bucket()

router = APIRouter(
    prefix="/api",
    tags=["Users"],
    )

@router.get("/users/attendance-logs")
async def get_all_user_attendance_logs(authorization: str = Depends(JWTBearer())):
    try:        
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )
    
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
        
        userAttendanceLogs = db.child("users_attendance_logs").get().val()
        userAttendanceLogs = dict(userAttendanceLogs)

        return JSONResponse(
            {
                "message": "OK",
                "operation_status": operationStatus.get("success"),
                "data": userAttendanceLogs,
            },
            status_code=200
        )

    except Exception as err:
        return JSONResponse(
            {
                "message": str(err)
            }
        )

@router.post("/users/attendance-logs")
async def insert_user_attendance_logs(user_id: int = Form(...), name: str = Form(...), floor: str = Form(...), status: str = Form(...), image_file: UploadFile = File(...)):

    try:
        userData = db.child("users").order_by_child("user_id").equal_to(user_id).get().val()
        
        nodesName = next(iter(userData))

        floor = floor
        status = status
        timestamp = datetime.now(ZoneInfo('Asia/Jakarta'))
        captured_image = image_file

        attendanceTime = db.child("users_attendance_logs").child(nodesName).child(timestamp.strftime("%Y-%m-%d")).get().val()

        if attendanceTime:
            return JSONResponse(
            {
            "message": f"User is already attended!",
            "operation_status": operationStatus.get("repoError"),
            },
            status_code = 409
            )
        
        uploadCapturedImage = await upload_captured_image(captured_image, user_id)
        getCapturedImageURL = uploadCapturedImage.body
        getCapturedImageURL = json.loads(getCapturedImageURL)

        capturedImageURL = getCapturedImageURL["image_url"]

        data = {
            "user_id": user_id,
            "name": name,
            "floor": floor,
            "status": status,
            "timestamp": timestamp.strftime("%a, %d %b %Y %H:%M"),
            "captured_face_url": capturedImageURL,
        }
                
        insertData = db.child("users_attendance_logs").child(nodesName).child(timestamp.strftime("%Y-%m-%d")).set(data)
        fcmToken = db.child("users").child(nodesName).get().val()["fcm_token"]
        
        #send notification
        sendNotification = send_notification(fcmToken, capturedImageURL)

        return JSONResponse(
            {
                "message": "Data has been successfully added!",
                "operation_status": operationStatus.get("success"),
                "data": data
             },
            status_code = 201
            )
    
    except Exception as err:
        return JSONResponse(
            {
                "message": str(err),
                "data": None,
            }, status_code=500
            )

@router.put("/users/me/profile-picture")
async def update_user_profile_pict(profile_pict: UploadFile = File(None), authorization: str = Depends(JWTBearer())):
    
    try:        
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )
        
        nodesName = jwtPayload["user_id"]
        userData = db.child('users').child(nodesName).get().val()
        userId = dict(userData)["user_id"]
        
        uploadProfilePict = await upload_profile_picture(userId, profile_pict, authorization)
        uploadProfilePictData = uploadProfilePict.body
        uploadProfilePictData = json.loads(uploadProfilePictData)

        profilePictURL = uploadProfilePictData
        data = {
                'profile_pict_url': profilePictURL["profile_picture_url"],
                }

        if profilePictURL["operation_status"] == operationStatus.get("fieldValidationError"):
            return JSONResponse(
            {
                "message": "There is no data sent!",
                "operation_status": operationStatus.get("fieldValidationError"),
                "data": None
            },
            status_code=422
            )
        
        updateData = db.child("users").child(nodesName).update(data)
        
        
        return JSONResponse(
            {
                "message": "User data has been successfully updated!",
                "operation_status": operationStatus.get("success"),
                "data": data
            },
            status_code=201
        )

    except Exception as err:
        return JSONResponse(
            {
                "message": str(err),
                "data": None
            },
            status_code=400
        )

@router.get("/users/me/attendance-logs/")
async def get_user_attendance_logs_by_month(month: int, authorization: str = Depends(JWTBearer())):

    try:
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )

        userId = jwtPayload["user_id"]

        dataAttendance = []
        getAttendances = db.child("users_attendance_logs").child(userId).get().val()
        extractedAttendances = dict(getAttendances)
        

        for date, attendance in extractedAttendances.items():
            convertedTimestamp = datetime.strptime(attendance["timestamp"], "%a, %d %b %Y %H:%M")
            
            if convertedTimestamp.month == month:
                dataAttendance.append(attendance)
        
        if not dataAttendance:
            return JSONResponse(
            {
            "message": "Attendance data for the selected month is not yet available",
            "operation_status": operationStatus.get("dataNotFound"),
            "data": dataAttendance,
            }, status_code=404
            )
        
        return JSONResponse(
            {
            "message": "OK",
            "operation_status": operationStatus.get("success"),
            "data": dataAttendance,
            }, status_code=200
            )
    
    except Exception as err:
        return JSONResponse(
            {
            "message": str(err),
            "data": None,
            }, status_code=500
            )

@router.delete("/users/me/attendance-logs/{user_id}")
async def delete_latest_user_attendance_log(user_id: int, authorization: str = Depends(JWTBearer())):

    try:
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )

        userId = jwtPayload["user_id"]

        getAttendances = db.child("users_attendance_logs").child(userId).get().val()
        extractedAttendances = dict(getAttendances)
        

        for date, attendance in extractedAttendances.items():
            convertedTimestamp = datetime.strptime(attendance["timestamp"], "%a, %d %b %Y %H:%M")
            currentDate = datetime.date(datetime.now())
            formattedConvertedTimestamp = convertedTimestamp.strftime("%Y-%m-%d")

            if formattedConvertedTimestamp == currentDate.strftime("%Y-%m-%d"):

                latestCapturedImageTime = convertedTimestamp.strftime("%Y-%m-%d_%H:%M")
                capturedImageFile = f"notification_{user_id}_{latestCapturedImageTime}"

                userDataDeletion = db.child("users_attendance_logs").child(userId).child(currentDate).remove()
                capturedImageDeletion = bucket.blob(f"captured_images/{capturedImageFile}").delete()

                return JSONResponse(
                {
                "message": "User's attendance log has been successfully deleted",
                "operation_status": operationStatus.get("success"),
                }, status_code=200
                )
            print("lol")
        return JSONResponse(
        {
        "message": "User's today's attendance data is not yet available",
        "operation_status": operationStatus.get("dataNotFound"),
        }, status_code=404
        )
    
    except Exception as err:
        return JSONResponse(
            {
            "message": str(err),
            "data": None,
            }, status_code=500
            )

@router.get("/users/me/attendance-logs")
async def get_user_attendance_logs(authorization: str = Depends(JWTBearer())):

    try:
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )

        userId = jwtPayload["user_id"]

        # childNode = db.child("users_attendance_logs").child(getUserId).shallow().get().val()

        # if childNode is None:
        #     return JSONResponse(
        #     {
        #     "message": "User does not have any attendance logs",
        #     "operation_status": operationStatus.get("repoError"),
        #     "data": None,
        #     }, status_code=200
        #     )

        dataAttendance = []
        getAttendances = db.child("users_attendance_logs").child(userId).get().val()
        extractedAttendances = dict(getAttendances)

        for date, attendance in extractedAttendances.items():
            dataAttendance.append(attendance)
            

        # for childNode in list(childNode):
        #     print(childNode)
        #     getAttendances = db.child("users_attendance_logs").child(getUserId).child(childNode).get().val()
            
        #     dataAttendance[childNode] = dict(getAttendances)
        
        return JSONResponse(
            {
            "message": "OK",
            "operation_status": operationStatus.get("success"),
            "data": dataAttendance,
            }, status_code=200
            )
    
    except Exception as err:
        return JSONResponse(
            {
            "message": str(err),
            "data": None,
            }, status_code=500
            )

@router.get("/users/me/attendance-status")
async def get_user_attendance_status(authorization: str = Depends(JWTBearer())):
    try:
        timestamp = datetime.now(ZoneInfo('Asia/Jakarta'))
        currentDate = timestamp.strftime("%Y-%m-%d")

        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )

        getUserId = jwtPayload["user_id"]

        childNode = db.child("users_attendance_logs").child(getUserId).shallow().get().val()

        userLastAttendanceDate = list(childNode)[-1]
        
        if userLastAttendanceDate != currentDate:
            return JSONResponse(
            {
            "message": "The user has not checked in yet",
            "operation_status": operationStatus.get("success"),
            "attendance_status": "absent",
            }, status_code=200
            )
        
        return JSONResponse(
            {
            "message": "The user has checked in",
            "operation_status": operationStatus.get("success"),
            "attendance_status": "present",
            }, status_code=200
            )
        
    except Exception as err:
        return JSONResponse(
            {"message": str(err),
            "data": None,
            }, status_code=200
            )

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int = Path(...), authorization: str = Depends(JWTBearer())):
    try:
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )
        
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
        
        userData = db.child("users").order_by_child("user_id").equal_to(user_id).get().val()

        if not userData:
            return JSONResponse(
            {
            "message": f"There is no user with user id {user_id}",
            "operation_status": operationStatus.get("repoError"),
            "data": None
            }, 
            status_code=400
            )
        
        nodesName = next(iter(userData))
        getUsers = db.child("users").child(nodesName).get().val()
        
        return JSONResponse(
            {
            "message":"success",
            "operation_status": operationStatus.get("success"),
            "data": getUsers
            }, 
            status_code=200
            )
    
    except Exception as err:
        return JSONResponse(
            {
            "message": str(err),
            "data": None
            }, 
            status_code=400
            )

@router.put("/users/{user_id}")
async def update_user(profile_pict: UploadFile = File(None), userData: updateUserSchema = Depends(validate_update_user_form), user_id: int = Path(...), authorization: str = Depends(JWTBearer())):
    
    try:        
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )
        
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
        
        uploadProfilePict = await upload_profile_picture(user_id, profile_pict, authorization)
        uploadProfilePictData = uploadProfilePict.body
        uploadProfilePictData = json.loads(uploadProfilePictData)

        profilePictURL = uploadProfilePictData
        data = userData.model_dump(exclude_none=True)
        
        if profilePictURL["operation_status"] == operationStatus.get("success"):
            data["profile_pict_url"] = profilePictURL["profile_picture_url"]

        if not data:
            return JSONResponse(
            {
                "message": "There is no data sent!",
                "operation_status": operationStatus.get("fieldValidationError"),
                "data": None
            },
            status_code=422
            )
        
        userData = db.child("users").order_by_child("user_id").equal_to(user_id).get().val()
        nodesName = next(iter(userData))
        
        updateData = db.child("users").child(nodesName).update(data)
        
        
        return JSONResponse(
            {
                "message": "User data has been successfully updated!",
                "operation_status": operationStatus.get("success"),
                "data": data
            },
            status_code=201
        )

    except Exception as err:
        return JSONResponse(
            {
                "message": str(err),
                "data": None
            },
            status_code=400
        )

@router.delete("/users/{user_id}")
async def delete_user_by_id(user_id: int = Path(...), authorization: str = Depends(JWTBearer())):
    # try:
        jwtPayload = decode_jwt(authorization)

        if jwtPayload == operationStatus.get("jwtExpiredToken"):
            return JSONResponse(
                {
                    "message": "JWT Token is expired",
                    "operation_status": operationStatus.get("jwtExpiredToken"),
                },
                status_code=401
            )
        
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
        
        userData = db.child("users").order_by_child("user_id").equal_to(user_id).get().val()
        nodesName = next(iter(userData))
        
        extractedUserData = dict(userData)
        userId = extractedUserData[nodesName]["user_id"]
        print(extractedUserData)
        
        userDataDeletion = db.child("users").child(nodesName).remove()
        userProfilePictDeletion = bucket.blob(f"profile_pictures/{userId}_profile_picture.jpg").delete()
        userAccountDeletion = auth.delete_user(nodesName)
        print(userDataDeletion)
        print(userProfilePictDeletion)
        print(userAccountDeletion)
        #tambahin kode untuk ngapus data profile picture (format nama profile picture harus diubah juga)

        return JSONResponse(
                    {
                        "message": "User data has been successfully deleted!",
                        "operation_status": operationStatus.get("success"),
                        # "data": data
                    },
                    status_code=200
                )
    
    # except Exception as err:
    #     return JSONResponse(
    #         {
    #             "message": str(err),
    #             "data": None
    #         },
    #         status_code=500
    #     )


@router.get("/users")
async def get_all_users(authorization: str = Depends(JWTBearer())):
    jwtPayload = decode_jwt(authorization)

    if jwtPayload == operationStatus.get("jwtExpiredToken"):
        return JSONResponse(
            {
                "message": "JWT Token is expired",
                "operation_status": operationStatus.get("jwtExpiredToken"),
            },
            status_code=401
        )
    
    # pake operation status buat handle error jwt yang expired
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
    
    getUsers = db.child("users").get().val()
    
    return JSONResponse(
        {
        "message":"OK",
        "operation_status": operationStatus.get("success"),         
        "data": getUsers
        }, 
        status_code=200)
    
