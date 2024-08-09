from fastapi.responses import JSONResponse
from firebase_admin import messaging
from constants.operation_status import operationStatus
from dotenv import load_dotenv

load_dotenv()

def send_notification(fcm_token: str):

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title="Konfirmasi Kehadiran Anda",
                body="Kami mendeteksi kehadiran Anda. Harap periksa dan verifikasi identitas Anda."
            ),
            token=fcm_token,
        )

        response = messaging.send(message)

        return JSONResponse(
                {
                    "message": "Notification has been sent",
                    "operation_status": operationStatus.get("success"),
                },
                status_code=200
            )
    
    except Exception as err:
        return JSONResponse(
                    {
                        "message": str(err),
                        "operation_status": operationStatus.get("sendNotificationError"),
                    },
                    status_code=500
                )

