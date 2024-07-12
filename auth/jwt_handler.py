import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv
from constants.operation_status import operationStatus

load_dotenv()

secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHMS")
expire_time = float(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

def encode_jwt(user_id: str, email: str, role: int, user_id_token: str):
    expires = datetime.now(timezone.utc) + timedelta(minutes=expire_time)
    
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "user_id_token": user_id_token, # needed for uploading file
        "sub": user_id,
        "identity": email,
        "exp_time": expires.strftime("%Y-%m-%d %H:%M:%S") 
    }
    return jwt.encode(payload, key=secret_key)

def decode_jwt(token: str):
    decoded_token = jwt.decode(token, key=secret_key, algorithms=algorithm)
    
    exp_time = datetime.strptime(decoded_token["exp_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    # print(type(decoded_token))
    # return decoded_token
    if exp_time >= datetime.now(timezone.utc).replace(tzinfo=timezone.utc):
        return decoded_token 
    else:
        return operationStatus.get("jwtExpiredToken")

# result = encode_jwt("12")
# print(timedelta(minutes=15))
# print(datetime.now(timezone.utc)+timedelta(seconds=120))

# print(jws.decode(result, secret_key, algorithms=['HS256']))
# print(result)

# print(decode_jwt(result))


