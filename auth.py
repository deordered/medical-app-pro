from google.auth.transport import requests
from google.oauth2 import id_token
from fastapi import HTTPException, status, APIRouter, Request
from fastapi.responses import RedirectResponse
import os
from models import User
import logging

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Set up router
router = APIRouter()
logger = logging.getLogger(__name__)

# Route to initiate Google OAuth2 login
@router.get("/login")
async def login():
    auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code"
        f"&scope=openid email profile&access_type=offline&prompt=consent"
    )
    logger.info("Redirecting user to Google OAuth2 for authentication")
    return RedirectResponse(auth_url)

# Route to handle Google OAuth2 callback
@router.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not found in the request"
        )
    try:
        id_info = id_token.verify_oauth2_token(code, requests.Request(), GOOGLE_CLIENT_ID)
        
        user = User.get_user_by_google_id(id_info["sub"]) or User.create_user(google_user_id=id_info["sub"], email=id_info.get("email"))
        
        return {"message": "User authenticated successfully", "user": user}
    except Exception as e:
        logger.error(f"Error in user authentication: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while authenticating")

