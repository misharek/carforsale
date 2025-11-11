import os
import motor.motor_asyncio
from dotenv import load_dotenv

# Завантажуємо змінні оточення з файлу .env
load_dotenv()

# Отримуємо посилання на MongoDB
MONGO_URI = os.getenv("MONGO_URI")
# Назва вашої бази даних (вона створиться автоматично)
DB_NAME = "car_bot_db"

# Створюємо асинхронний клієнт Motor
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

# Отримуємо об'єкт бази даних
db = client[DB_NAME]

# Отримуємо колекції (згідно з вашими схемами)
# 👤 Колекція користувачів
users_collection = db["users"]

# 🚗 Колекція автомобілів
cars_collection = db["cars"]

print("✅ З'єднано з MongoDB")
