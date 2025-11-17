import pytest
# Додаємо MagicMock
from unittest.mock import AsyncMock, MagicMock

# Імпортуємо код, який хочемо протестувати
from handlers.sell.sell_fsm import handle_brand
from handlers.sell.sell_states import SellCarFSM

# --- Допоміжний клас для імітації об'єкта Message ---
class MockMessage:
    def __init__(self, text):
        self.text = text
        # Метод .answer() має бути асинхронним моком
        self.answer = AsyncMock()

# -----------------------------------------------
# ТЕСТ: Перевірка обробника 'handle_brand'
# -----------------------------------------------
@pytest.mark.asyncio
async def test_handle_brand_normalization():
    """
    Перевіряємо, що обробник 'handle_brand':
    1. Правильно нормалізує текст ( "bmw" -> "BMW" ).
    2. Зберігає дані у стан (state).
    3. Перемикає FSM на наступний крок (enter_model).
    """
    print("Запуск test_handle_brand_normalization...")
    
    # 1. Готуємо "фальшиві" об'єкти
    message = MockMessage(text="  bmw  ") 
    
    # === ВИПРАВЛЕННЯ ТУТ ===
    # Створюємо звичайний MagicMock
    mock_state = MagicMock() 
    # Його методи .update_data та .set_state робимо АСИНХРОННИМИ
    mock_state.update_data = AsyncMock()
    mock_state.set_state = AsyncMock()
    # ========================

    # 2. Викликаємо наш обробник
    await handle_brand(message, mock_state)

    # 3. Перевіряємо результат
    
    # Перевіряємо, що .update_data був викликаний з коректними даними
    mock_state.update_data.assert_called_once_with(brand="BMW")
    
    # Перевіряємо, що FSM перемкнувся на правильний стан
    mock_state.set_state.assert_called_once_with(SellCarFSM.enter_model)

    # Перевіряємо, що бот відповів користувачу
    message.answer.assert_called_once()
    
    print("test_handle_brand_normalization -> OK")