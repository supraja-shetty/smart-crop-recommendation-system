import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret123")
    MYSQL_HOST = os.getenv("DB_HOST", "localhost")
    MYSQL_USER = os.getenv("DB_USER", "root")
    MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "Supraja@123")
    MYSQL_DB = os.getenv("DB_NAME", "crop_db")
    MYSQL_PORT = int(os.getenv("DB_PORT", 3306))
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
