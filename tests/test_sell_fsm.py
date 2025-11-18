import pytest
from unittest.mock import AsyncMock, MagicMock
from handlers.sell.sell_fsm import handle_brand
from handlers.sell.sell_states import SellCarFSM

class MockMessage:
    def __init__(self, text):
        self.text = text
        self.answer = AsyncMock()

@pytest.mark.asyncio
async def test_handle_brand_normalization():
    print("Запуск test_handle_brand_normalization...")
    
    message = MockMessage(text="  bmw  ") 
    
    mock_state = MagicMock() 
    mock_state.update_data = AsyncMock()
    mock_state.set_state = AsyncMock()

    await handle_brand(message, mock_state)


    mock_state.update_data.assert_called_once_with(brand="BMW")
    
    mock_state.set_state.assert_called_once_with(SellCarFSM.enter_model)

    message.answer.assert_called_once()
    
    print("test_handle_brand_normalization -> OK")