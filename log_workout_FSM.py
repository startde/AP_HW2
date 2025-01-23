from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from create_profile_FSM import data_manager

router_workout = Router()

class WorkoutLog(StatesGroup):
    waiting_for_type = State()
    waiting_for_duration = State()

@router_workout.message(Command("log_workout"))
async def cmd_log_workout(message: Message, state: FSMContext):
    # Проверяем наличие профиля
    user_id = str(message.from_user.id)
    if user_id not in data_manager.users:
        await message.answer("❌ Сначала создайте профиль с помощью /set_profile")
        return
        
    available_workouts = data_manager.get_available_workouts()
    await message.answer(
        "🏃‍♂️ Укажите тип тренировки:\n\n" + 
        "\n".join([f"• {w}" for w in available_workouts])
    )
    await state.set_state(WorkoutLog.waiting_for_type)

@router_workout.message(WorkoutLog.waiting_for_type)
async def process_workout_type(message: Message, state: FSMContext):
    workout_type = message.text.lower()
    
    if workout_type not in data_manager.get_available_workouts():
        available_workouts = data_manager.get_available_workouts()
        await message.answer(
            "❌ Неверный тип тренировки. Выберите из списка:\n\n" + 
            "\n".join([f"• {w}" for w in available_workouts])
        )
        return
    
    await state.update_data(workout_type=workout_type)
    await message.answer("⏱ Введите продолжительность тренировки в минутах:")
    await state.set_state(WorkoutLog.waiting_for_duration)

@router_workout.message(WorkoutLog.waiting_for_duration)
async def process_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text)
        
        if duration <= 0:
            await message.answer("❌ Продолжительность должна быть положительным числом")
            return

        data = await state.get_data()
        workout_type = data['workout_type']
        user_id = str(message.from_user.id)
        
        result = data_manager.log_workout(user_id, workout_type, duration)
        
        if "error" in result:
            await message.answer(f"❌ Ошибка: {result['error']}")
        else:
            await message.answer(
                f"✅ Тренировка записана!\n\n"
                f"🏃‍♂️ {result['workout_type'].capitalize()}: {result['duration']} минут\n"
                f"🔥 Сожжено калорий: {result['calories_burned']}\n"
                f"💧 Рекомендация: выпейте {result['water_recommendation']} мл воды\n\n"
                f"📊 Статистика за день:\n"
                f"• Потреблено калорий: {result['daily_stats']['calories_consumed']}\n"
                f"• Сожжено калорий: {result['daily_stats']['total_calories_burned']}\n"
                f"• Баланс калорий: {result['daily_stats']['calories_balance']}"
            )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите целое число минут")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()