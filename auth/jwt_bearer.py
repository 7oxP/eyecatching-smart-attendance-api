from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import decode_jwt
from constants.operation_status import operationStatus

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                return JSONResponse(
                    {
                    "message": "Invalid authentication scheme",
                    "operation_status": operationStatus.get("jwtGenerateError"),
                    },
                    status_code=403)
            if not self.verify_jwt(credentials.credentials):
                return JSONResponse(
                    {
                    "message": "Invalid token or expired token",
                    "operation_status": operationStatus.get("jwtGenerateError"),
                    },
                    status_code=403)            
            return credentials.credentials
        else:
            return JSONResponse(
                    {
                    "message": "Invalid authorization code",
                    "operation_status": operationStatus.get("jwtGenerateError"),
                    },
                    status_code=403)  

    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = decode_jwt(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid
