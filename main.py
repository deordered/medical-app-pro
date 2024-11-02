from fastapi import FastAPI, HTTPException, status, Query
from pymongo import MongoClient
from auth import router as auth_router
from payment import router as payment_router
from dotenv import load_dotenv
import uvicorn
import os
import logging
from query import process_query

# Load environment variables and initialize logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI app instance
app = FastAPI()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["mydatabase"]
users_collection = db["users"]

@app.post("/query")
async def query_endpoint(
    query: str = Query(..., min_length=3, max_length=500, regex=r'^[a-zA-Z0-9\s?.,-]+$'),
    user_email: str = Query(..., description="The email of the user making the query")
):
    user = users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    query_limit = 70 if user.get("is_subscriber") else 3
    current_query_count = user.get("query_count", 0)

    if current_query_count >= query_limit:
        logger.warning(f"User {user['google_user_id']} exceeded query limit.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Query limit exceeded for the day."
        )

    try:
        response = process_query(query)
        logger.info(f"Query processed for user {user['google_user_id']}")

        users_collection.update_one(
            {"google_user_id": user["google_user_id"]},
            {"$inc": {"query_count": 1}}
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing query"
        )

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(payment_router, prefix="/payment", tags=["Payment"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
