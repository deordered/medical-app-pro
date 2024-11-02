from pydantic import BaseModel, EmailStr
from typing import Optional
from database import db

class User:
    @staticmethod
    def get_user_by_google_id(google_user_id: str):
        return db["users"].find_one({"google_user_id": google_user_id})

    @staticmethod
    def create_user(google_user_id: str, email: str):
        user_data = {
            "google_user_id": google_user_id,
            "email": email,
            "is_subscriber": False,
            "query_count": 0
        }
        db["users"].insert_one(user_data)
        return user_data

    @staticmethod
    def update_user_query_count(google_user_id: str, query_count: int):
        db["users"].update_one({"google_user_id": google_user_id}, {"$set": {"query_count": query_count}})

    @staticmethod
    def get_or_create_user(google_user_id: str, email: str):
        user = User.get_user_by_google_id(google_user_id)
        return user or User.create_user(google_user_id, email)

    @staticmethod
    def update_subscription_status(google_user_id: str, is_subscriber: bool):
        db["users"].update_one({"google_user_id": google_user_id}, {"$set": {"is_subscriber": is_subscriber}})

# Pydantic model for user data validation
class UserCreateModel(BaseModel):
    google_user_id: str
    email: EmailStr
    is_subscriber: Optional[bool] = False
    query_count: Optional[int] = 0

class UserResponseModel(BaseModel):
    google_user_id: str
    email: EmailStr
    is_subscriber: bool
    query_count: int
