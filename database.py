from pydantic import BaseModel, EmailStr
from typing import Optional
from pymongo import MongoClient, errors
import logging

# Initialize MongoDB connection and logging
client = MongoClient("mongodb://localhost:27017")
db = client["mydatabase"]
users_collection = db["users"]
logger = logging.getLogger(__name__)

class User:
    @staticmethod
    def get_user_by_google_id(google_user_id: str):
        try:
            user = users_collection.find_one({"google_user_id": google_user_id})
            logger.info(f"Retrieved user for Google ID {google_user_id}")
            return user
        except errors.PyMongoError as e:
            logger.error(f"Error retrieving user by Google ID {google_user_id}: {e}")
            return None

    @staticmethod
    def create_user(google_user_id: str, email: str):
        user_data = {
            "google_user_id": google_user_id,
            "email": email,
            "is_subscriber": False,
            "query_count": 0
        }
        try:
            users_collection.insert_one(user_data)
            logger.info(f"Created new user with Google ID {google_user_id}")
            return user_data
        except errors.PyMongoError as e:
            logger.error(f"Error creating user with Google ID {google_user_id}: {e}")
            return None

    @staticmethod
    def update_user_query_count(google_user_id: str, query_count: int):
        try:
            users_collection.update_one(
                {"google_user_id": google_user_id},
                {"$set": {"query_count": query_count}}
            )
            logger.info(f"Updated query count for Google ID {google_user_id}")
        except errors.PyMongoError as e:
            logger.error(f"Error updating query count for Google ID {google_user_id}: {e}")

    @staticmethod
    def update_subscription_status(google_user_id: str, is_subscriber: bool):
        try:
            users_collection.update_one(
                {"google_user_id": google_user_id},
                {"$set": {"is_subscriber": is_subscriber}}
            )
            logger.info(f"Updated subscription status for Google ID {google_user_id}")
        except errors.PyMongoError as e:
            logger.error(f"Error updating subscription status for Google ID {google_user_id}: {e}")

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
