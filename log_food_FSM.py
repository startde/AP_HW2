from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from create_profile_FSM import data_manager
from utils import get_food_info

router_food = Router()

class FoodLog(StatesGroup):
    waiting_for_amount = State()

@router_food.message(Command("log_food"))
async def log_food(message: Message, state: FSMContext):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer(
                "⚠️ Используйте формат: /log_food <название продукта>\n"
                "Например: /log_food apple"
            )
            return

        food_name = ' '.join(parts[1:]).lower()
        user_id = str(message.from_user.id)

        if user_id not in data_manager.users:
            await message.answer("❌ Сначала создайте профиль с помощью /set_profile")
            return

        # Получаем информацию о продукте через API
        food_info = await get_food_info(food_name)
        
        if not food_info:
            await message.answer(
                "❌ Продукт не найден в базе данных\n"
                "Попробуйте указать название на английском языке"
            )
            return

        await state.update_data(food_name=food_name)
        
        await state.set_state(FoodLog.waiting_for_amount)
        
        await message.answer(
            f"🍴 {food_info.product_name}\n"
            f"Калорийность: {round(food_info.calories)} ккал на 100 г\n"
            f"Укажите количество грамм:"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка: {str(e)}\n"
            "Используйте формат: /log_food <название продукта>"
        )

@router_food.message(FoodLog.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        
        if amount <= 0:
            await message.answer("❌ Количество должно быть положительным числом")
            return
        
        data = await state.get_data()
        food_name = data['food_name']
        
        user_id = str(message.from_user.id)
        result = await data_manager.log_food(user_id, food_name, amount)
        
        if "error" in result:
            await message.answer(f"❌ Ошибка: {result['error']}")
        else:
            await message.answer(
                f"✅ Записано:\n"
                f"🍴 {result['food']}\n"
                f"⚖️ Количество: {result['amount']} г\n"
                f"🔥 Калорийность порции: {round(result['calories'])} ккал\n"
                f"📊 Всего калорий за сегодня: {round(result['total_calories'])} ккал"
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()
