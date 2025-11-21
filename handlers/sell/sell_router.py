import logging
import asyncio
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import user_manager
from database import car_manager
from .sell_states import SellCarFSM, SellerFSM 

sell_router = Router()

# --- Допоміжна функція для тимчасових повідомлень ---
async def show_temp_message(message: Message, text: str, delay: int = 3):
    msg = await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

# ==========================================
# 1. СТАРТ ПРОДАЖУ
# ==========================================
@sell_router.message(Command("sell"))
async def handle_sell_command(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass

    data = await state.get_data()
    old_menu_id = data.get("main_menu_id")
    if old_menu_id:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=old_menu_id)
        except: pass
    
    user = await user_manager.get_user_by_id(message.from_user.id)
    if user is None:
        button_text = "⚠️ Зареєструватися та почати"
        message_text = "Вітаю! Ви тут вперше. Натисніть кнопку для реєстрації."
    else:
        button_text = "🚗 Розмістити нове оголошення"
        message_text = f"Раді бачити, {user['full_name']}! Продамо авто?"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="sell_car")],
            [InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")]
        ]
    )
    await message.answer(message_text, reply_markup=keyboard, parse_mode=None)


# ==========================================
# 2. РЕЄСТРАЦІЯ ТА ПЕРЕВІРКА
# ==========================================
@sell_router.callback_query(F.data == "sell_car")
async def handle_sell_car(callback: CallbackQuery, state: FSMContext):
    try:
        try: await callback.message.delete()
        except: pass

        user_data = callback.from_user
        user = await user_manager.get_or_create_user(
            telegram_id=user_data.id,
            full_name=user_data.first_name,
            username=user_data.username,
        )

        alert_text = None
        if user["role"] == "buyer":
            await user_manager.set_user_role_seller(user_data.id, full_name=user_data.full_name)
            user["role"] = "seller"
            alert_text = "✅ Ви тепер зареєстровані як Продавець!"

        if user.get("phone_number") is None:
            if alert_text: await callback.answer(alert_text, show_alert=True)
            else: await callback.answer()

            await state.set_state(SellerFSM.enter_phone)
            
            contact_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
                    [KeyboardButton(text="❌ Скасувати")]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            
            request_msg = await callback.message.answer(
                "❗️ **Потрібен Ваш контакт.**\n\n"
                "Щоб покупці могли з Вами зв'язатися, поділіться, будь ласка, номером телефону:",
                reply_markup=contact_kb
            )
            await state.update_data(phone_request_id=request_msg.message_id)
            # Зберігаємо ID повідомлення, щоб видалити його при скасуванні
            await state.update_data(last_bot_msg_id=request_msg.message_id)
            return
            
        if alert_text: await callback.answer(alert_text, show_alert=True)
        else: await callback.answer()

        await state.set_state(SellCarFSM.enter_brand)
        
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Скасувати")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        # 🔥 ЗМІНА: Зберігаємо об'єкт повідомлення у змінну msg
        msg = await callback.message.answer(
            "🚗 **Створення оголошення**\n\n"
            "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):",
            reply_markup=cancel_kb
        )
        # 🔥 ЗМІНА: Записуємо ID цього повідомлення в state
        await state.update_data(last_bot_msg_id=msg.message_id)

    except Exception as e:
        logging.error(f"Помилка sell_car: {e}", exc_info=True)
        await callback.message.answer("❌ Помилка бази даних.")
        await callback.answer()


# ==========================================
# 3. ОБРОБКА ТЕЛЕФОНУ
# ==========================================
@sell_router.message(SellerFSM.enter_phone, F.contact | F.text)
async def handle_phone_request(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass

    data = await state.get_data()
    request_msg_id = data.get("phone_request_id")
    if request_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=request_msg_id)
        except:
            pass 

    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text:
        if message.text == "❌ Скасувати": 
            return # Це обробить sell_fsm
        phone_number = message.text.strip()
    else:
        # Якщо це не текст і не контакт, видалимо і це
        msg = await message.answer("⚠️ Скористайтеся кнопкою або введіть номер.", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(3)
        try: await msg.delete()
        except: pass
        return

    user_full_name = message.from_user.full_name
    await user_manager.update_user_phone(
        telegram_id=message.from_user.id, 
        phone_number=phone_number,
        full_name=user_full_name
    )
    
    await state.update_data(phone_request_id=None) 
    
    temp_success = await message.answer(
        f"✅ Номер {phone_number} збережено!\nРеєстрацію завершено.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await state.set_state(SellCarFSM.enter_brand)
    
    await asyncio.sleep(3)
    try: await temp_success.delete()
    except: pass

    cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Скасувати")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    
    # 🔥 ЗМІНА: Тут теж зберігаємо ID повідомлення
    msg = await message.answer(
        "🚗 **Створення оголошення**\n\n"
        "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):",
        reply_markup=cancel_kb
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


# ==========================================
# 4. МОЇ ОГОЛОШЕННЯ (/my_ads)
# ==========================================
@sell_router.message(Command("my_ads"))
async def handle_my_ads_command(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass

    data = await state.get_data()
    old_menu_id = data.get("main_menu_id")
    if old_menu_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_menu_id)
        except: pass
    
    await state.update_data(main_menu_id=None)

    seller_id = message.from_user.id
    ads = await car_manager.find_car_ads(query={"seller_id": seller_id}, limit=100) 
    
    if not ads:
        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Розмістити оголошення", callback_data="sell_car")],
                [InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")]
            ]
        )
        msg = await message.answer("📂 У вас поки немає активних оголошень.", reply_markup=back_kb)
        # Можна зберегти як меню, щоб потім видалити
        await state.update_data(main_menu_id=msg.message_id)
        return

    response_text = "⭐️ **Ваші активні оголошення:** ⭐️\n\n"
    keyboard_buttons = []
    
    for i, ad in enumerate(ads, 1):
        ad_id = str(ad['_id'])
        response_text += f"*{i}. {ad['brand']} {ad['model']}* ({ad['year']}) — ${ad['price']}\n"
        delete_button = InlineKeyboardButton(
            text=f"❌ Видалити #{i}",
            callback_data=f"delete_ad_{ad_id}"
        )
        keyboard_buttons.append([delete_button])

    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    msg = await message.answer(response_text, reply_markup=keyboard, parse_mode='Markdown')
    await state.update_data(main_menu_id=msg.message_id)


@sell_router.callback_query(F.data.startswith("delete_ad_"))
async def handle_delete_ad(callback: CallbackQuery):
    ad_id = callback.data.split("_")[-1]
    success = await car_manager.delete_car_ad(ad_id)
    
    if success:
        await callback.answer("✅ Оголошення успішно видалено!", show_alert=True)
        await callback.message.edit_text("♻️ Список оновлюється...")
        await asyncio.sleep(1)
        try: await callback.message.delete()
        except: pass
    else:
        await callback.answer("❌ Помилка видалення.", show_alert=True)