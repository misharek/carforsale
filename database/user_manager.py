from ._db_connector import users_collection
from datetime import datetime


async def get_user_by_id(telegram_id: int):
    return await users_collection.find_one({"telegram_id": telegram_id})


async def get_or_create_user(telegram_id: int, full_name: str, username: str = None):
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
    Знаходить користувача за telegram_id та оновлює його роль на 'seller'.
    Це викликається, коли користувач натискає "Продати авто".
    """

    # Фільтр: який документ оновити
    filter_query = {"telegram_id": telegram_id}

    # Дані для оновлення: встановити нове значення для поля 'role'
    update_data = {"$set": {"role": "seller"}}

    # "await" - чекаємо, поки база оновить ОДИН документ
    result = await users_collection.update_one(filter_query, update_data)

    if result.modified_count > 0:
        print(f"👤 Роль для {telegram_id} оновлено на 'seller'")

    return result.modified_count > 0  # Поверне True, якщо оновлення відбулось


async def update_user_phone(telegram_id: int, phone_number: str):
    """
    Додає або оновлює номер телефону користувача.
    Це буде потрібно для продавців.
    """
    # Переконуємось, що номер телефону у правильному форматі (з +)
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    filter_query = {"telegram_id": telegram_id}
    update_data = {"$set": {"phone_number": phone_number}}

    result = await users_collection.update_one(filter_query, update_data)

    if result.modified_count > 0:
        print(f"📞 Телефон для {telegram_id} оновлено.")

    return result.modified_count > 0
