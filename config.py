import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """應用程式設定"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-very-bad-default-secret-key-for-dev-only')
    DVCBOT_API_KEY = os.getenv('DVCBOT_API_KEY')
    ASSISTANT_ID = os.getenv('ASSISTANT_ID')