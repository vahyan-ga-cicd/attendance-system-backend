import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY_ID")
    AWS_REGION = os.getenv("AWS_REGION")

    S3_BUCKET = os.getenv("S3_BUCKET")
    EMPLOYEE_TABLE = os.getenv("EMPLOYEE_TABLE")
    ATTENDANCE_TABLE = os.getenv("ATTENDANCE_TABLE")
    # COUNTERS_TABLE = os.getenv("COUNTERS_TABLE")

settings = Settings()