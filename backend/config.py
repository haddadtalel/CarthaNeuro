from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb+srv://kf_db_user:fawzi123@cn.esxvpar.mongodb.net/?appName=cn"
    MONGO_DB_NAME: str = "cn"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    # Upload directory for reports and files
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

settings = Settings()