from ._db_connector import users_collection
from datetime import datetime


async def get_user_by_id(telegram_id: int):
    """
    Знаходить користувача за його Telegram ID.
    """
    return await users_collection.find_one({"telegram_id": telegram_id})


async def get_or_create_user(telegram_id: int, full_name: str, username: str = None):
    """
    Знаходить існуючого користувача або створює нового з роллю 'buyer'.
    """
    user = await get_user_by_id(telegram_id)

    if user:
        return user
    else:
        new_user = {
            "telegram_id": telegram_id,
            "role": "buyer",
            "username": f"@{username}" if username else None,
            "full_name": full_name,
            "phone_number": None,
            "registration_date": datetime.utcnow(),
        }

        await users_collection.insert_one(new_user)

        print(f"🆕 Зареєстровано нового користувача: {full_name} ({telegram_id})")

        return new_user


async def set_user_role_seller(telegram_id: int):
    """
    Змінює роль користувача на 'seller'.
    """
    filter_query = {"telegram_id": telegram_id}
    update_data = {"$set": {"role": "seller"}}

    result = await users_collection.update_one(filter_query, update_data)

    if result.modified_count > 0:
        print(f"👤 Роль для {telegram_id} оновлено на 'seller'")

    return result.modified_count > 0


async def update_user_phone(telegram_id: int, phone_number: str, full_name: str = None):
    """
    Додає або оновлює номер телефону користувача.
    Включає логування імені.
    """
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    filter_query = {"telegram_id": telegram_id}
    update_data = {"$set": {"phone_number": phone_number}}

    result = await users_collection.update_one(filter_query, update_data)

    if result.modified_count > 0:
        log_info = full_name if full_name else telegram_id
        print(f"📞 Телефон для {log_info} оновлено.")

    return result.modified_count > 0