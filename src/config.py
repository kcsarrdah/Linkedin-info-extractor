import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
