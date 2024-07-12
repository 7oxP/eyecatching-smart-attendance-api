from config.firebase_config import firebase_config
import pyrebase
import os
from dotenv import load_dotenv

load_dotenv()

storageBucket = os.getenv("STORAGE_BUCKET")
credentialsJSON = os.getenv("CREDENTIALS_JSON")

firebase = pyrebase.initialize_app(firebase_config())
storage = firebase.storage()

def get_credentials():
    # path dikosongin karena ga ngasih efek apa-apa dan nama filenya harus beserta nama folder (kalau mau didownload di dalam folder)
    credentials = storage.child(credentialsJSON).download("", credentialsJSON)
    
    return credentials

