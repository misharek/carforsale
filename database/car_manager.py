from ._db_connector import cars_collection
from bson.objectid import ObjectId

async def add_car_ad(car_data: dict):
    """
    Зберігає словник даних про авто (зібраних FSM) у колекцію.
    """
    # data вже містить всі поля (brand, model, year, price, photo...)
    result = await cars_collection.insert_one(car_data)
    
    # Повертаємо унікальний ID, який призначила MongoDB
    return result.inserted_id

async def get_car_ad_by_id(ad_id: str):
    """
    Знаходить оголошення за його MongoDB ID.
    """
    try:
        # ObjectId потрібен для коректного пошуку за унікальним ID
        return await cars_collection.find_one({"_id": ObjectId(ad_id)})
    except:
        return None # Якщо ID некоректний або не знайдено

async def find_car_ads(query: dict = None, limit: int = 10, skip: int = 0):
    """
    Виконує пошук оголошень за заданим критерієм (query).
    """
    # query може бути {} (для всіх авто), {"brand": "BMW"}, {"price": {"$lt": 10000}} і т.д.
    
    # Створюємо курсор (потік даних)
    cursor = cars_collection.find(query or {})
    
    # Обмежуємо кількість результатів (пагінація)
    cursor = cursor.limit(limit).skip(skip).sort("_id", -1) # Сортування за ID (від нових до старих)
    
    # Перетворюємо курсор у список
    cars = await cursor.to_list(length=limit)
    return cars