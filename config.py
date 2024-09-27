import os
# from dotenv import load_dotenv

# For Development
# load_dotenv()
# JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Change this to a secure key
# AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# REGION_NAME = os.getenv("REGION_NAME")
# API_TOKEN = os.getenv("API_TOKEN")

# For Deployment
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.environ.get("REGION_NAME")
API_TOKEN = os.environ.get("API_TOKEN")
