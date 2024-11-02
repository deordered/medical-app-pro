import stripe
import os
from pymongo import MongoClient
from fastapi import HTTPException, status, APIRouter, Request
import logging

# Environment variables
stripe.api_key = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Initialize logging and database
logger = logging.getLogger(__name__)
client = MongoClient(MONGO_URI)
db = client["mydatabase"]
users_collection = db["users"]

# Payment router setup
router = APIRouter()

# Function to create Stripe Checkout Session
def create_stripe_checkout_session(user):
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_1XXXXXXX',  # Replace with your Stripe price ID for the subscription
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://your-domain.com/success',
            cancel_url='https://your-domain.com/cancel',
            client_reference_id=user["_id"],
        )
        logger.info(f"Checkout session created for user {user['_id']}")
        return checkout_session.url
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe error during checkout session creation"
        )

@router.post("/create-checkout-session")
async def create_checkout_session(user_email: str):
    user = users_collection.find_one({"email": user_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    checkout_url = create_stripe_checkout_session(user)
    return {"checkout_url": checkout_url}

@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        logger.info("Webhook event verified successfully")

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session.get('client_reference_id')
            users_collection.update_one({"_id": user_id}, {"$set": {"is_subscriber": True}})
            logger.info(f"User {user_id} subscription status updated to active")

        return {"status": "success"}
    except ValueError:
        logger.error("Invalid payload in webhook")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature for webhook event")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Unexpected error in webhook handling: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error while handling webhook event"
        )
