import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "car_bot_db"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

db = client[DB_NAME]

users_collection = db["users"]

cars_collection = db["cars"]

print("✅ З'єднано з MongoDB")
