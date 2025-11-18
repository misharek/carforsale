import logging
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


@sell_router.message(Command("sell"))
async def handle_sell_command(message: Message):
    user = await user_manager.get_user_by_id(message.from_user.id)
    if user is None:
        button_text = "⚠️ Зареєструватися та почати"
        message_text = "Вітаю! Ви тут вперше. Натисніть кнопку для реєстрації."
    else:
        button_text = "🚗 Розмістити нове оголошення"
        message_text = f"Раді бачити, {user['full_name']}! Продамо авто?"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="sell_car")]
        ]
    )
    await message.answer(message_text, reply_markup=keyboard)


@sell_router.callback_query(F.data == "sell_car")
async def handle_sell_car(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = callback.from_user
        user = await user_manager.get_or_create_user(
            telegram_id=user_data.id,
            full_name=user_data.first_name,
            username=user_data.username,
        )


        if user["role"] == "buyer":
            await user_manager.set_user_role_seller(user_data.id, full_name=user_data.full_name)
            user["role"] = "seller"
            await callback.message.answer("✅ Ви тепер зареєстровані як Продавець!")


        if user.get("phone_number") is None:
            await state.set_state(SellerFSM.enter_phone)
            
            contact_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await callback.message.answer(
                "❗️ **Потрібен Ваш контакт.**\n\n"
                "Щоб покупці могли з Вами зв'язатися, поділіться, будь ласка, номером телефону:",
                reply_markup=contact_kb
            )
            await callback.answer()
            return
            

        await state.set_state(SellCarFSM.enter_brand)
        await callback.message.answer(
            "🚗 **Створення оголошення**\n\n"
            "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):",
            reply_markup=ReplyKeyboardRemove()
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Помилка sell_car: {e}", exc_info=True)
        await callback.message.answer("❌ Помилка бази даних.")
        await callback.answer()


@sell_router.message(SellerFSM.enter_phone, F.contact | F.text)
async def handle_phone_request(message: Message, state: FSMContext):


    if message.contact:
        phone_number = message.contact.phone_number
        
    elif message.text:
        # Виправлено: беремо message.text
        phone_number = message.text.strip()
        
    else:
        await message.answer("Будь ласка, скористайтеся кнопкою 'Поділитися контактом' або введіть номер вручну.", 
                             reply_markup=ReplyKeyboardRemove())
        return

    user_full_name = message.from_user.full_name
    await user_manager.update_user_phone(
        telegram_id=message.from_user.id, 
        phone_number=phone_number,
        full_name=user_full_name
    )
    

    await state.clear()
    
    await message.answer(
        f"✅ Номер {phone_number} збережено.\n"
        "Тепер можемо почати розміщення оголошення.",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.set_state(SellCarFSM.enter_brand)
    await message.answer(
        "🚗 **Створення оголошення**\n\n"
        "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):"
    )


@sell_router.message(Command("myads"))
async def handle_my_ads(message: Message):
    seller_id = message.from_user.id
    
    ads = await car_manager.find_car_ads(query={"seller_id": seller_id}, limit=100) 
    
    if not ads:
        await message.answer("У вас немає активних оголошень для управління. Розмістіть перше!")
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(response_text, reply_markup=keyboard, parse_mode='Markdown')


@sell_router.callback_query(F.data.startswith("delete_ad_"))
async def handle_delete_ad(callback: CallbackQuery):
    ad_id = callback.data.split("_")[-1]
    
    success = await car_manager.delete_car_ad(ad_id)
    
    if success:
        new_text = f"✅ Оголошення #{ad_id[-5:]} успішно видалено." 
    else:
        new_text = "❌ Помилка: Не вдалося знайти або видалити оголошення."

    await callback.message.edit_text(new_text)
    await callback.answer(new_text, show_alert=True)