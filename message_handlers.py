from aiogram.types import Message,  FSInputFile
from aiogram import Router
from aiogram.filters import CommandStart, Command
from create_profile_FSM import router_create_profile, data_manager
from log_food_FSM import router_food
from log_workout_FSM import router_workout
import matplotlib.pyplot as plt
import os
from datetime import datetime


router = Router()
router.include_router(router_create_profile)
router.include_router(router_food)
router.include_router(router_workout)

# Создаем экземпляр DataManager без начального профиля


@router.message(CommandStart())
async def welcome_message(message: Message):
    await message.answer(
        text=f"Привет {message.from_user.first_name}!\n"
             "Это твой бот для расчёта нормы воды, калорий и трекинга активности\n\n"
             "Для начала работы настрой свой профиль командой /set_profile"
    )

@router.message(Command("log_water"))
async def log_water(message: Message):
    try:
        amount = float(message.text.split()[1])
        user_id = str(message.from_user.id)
        
        # Проверяем, есть ли пользователь в базе
        result = data_manager.log_water(user_id, amount)
        print(result)
        
        if "error" in result:
            await message.answer(
                "Сначала необходимо настроить профиль!\n"
                "Используйте команду /set_profile"
            )
            return
        
        await message.answer(
            f"💧 Записано: {result['logged']} мл воды\n"
            f"Всего за сегодня: {result['total']} мл\n"
            f"Осталось до нормы: {result['remaining']} мл"
        )
    except IndexError:
        await message.answer("Используйте формат: /log_water <количество в мл>")
    except ValueError:
        await message.answer("Количество воды должно быть числом")

async def create_progress_graphs(user_id: str) -> str:
    """Создает графики прогресса и возвращает путь к файлу"""
    
    progress = data_manager.get_progress(user_id)
    
    # Создаем фигуру с тремя графиками
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
    fig.suptitle('Ваш прогресс за сегодня', fontsize=16)
    
    # График потребления воды
    water_data = [0, progress['water']['consumed']]
    water_goal = [progress['water']['goal'], progress['water']['goal']]
    times = ['00:00', datetime.now().strftime('%H:%M')]
    
    ax1.plot(times, water_data, 'b-', label='Выпито воды')
    ax1.plot(times, water_goal, 'r--', label='Цель')
    ax1.fill_between(times, water_data, alpha=0.3)
    ax1.set_title('Потребление воды (мл)')
    ax1.legend()
    ax1.grid(True)
    
    # График калорий
    calories_consumed = [0, progress['calories']['consumed']]
    calories_goal = [progress['calories']['goal'], progress['calories']['goal']]
    calories_burned = [0, progress['calories']['burned']]
    
    ax2.plot(times, calories_consumed, 'g-', label='Потреблено')
    ax2.plot(times, calories_goal, 'r--', label='Цель')
    ax2.plot(times, calories_burned, 'b-', label='Сожжено')
    ax2.fill_between(times, calories_consumed, alpha=0.3)
    ax2.set_title('Калории (ккал)')
    ax2.legend()
    ax2.grid(True)
    
    # Круговая диаграмма распределения калорий по приемам пищи
    if progress['food_log']:
        foods = [entry['food'] for entry in progress['food_log']]
        calories = [entry['calories'] for entry in progress['food_log']]
        ax3.pie(calories, labels=foods, autopct='%1.1f%%')
        ax3.set_title('Распределение калорий по приемам пищи')
    else:
        ax3.text(0.5, 0.5, 'Нет данных о приемах пищи', 
                 horizontalalignment='center', verticalalignment='center')
    
    # Сохраняем график
    plt.tight_layout()
    graph_path = f'user_{user_id}_progress.png'
    plt.savefig(graph_path)
    plt.close()
    
    return graph_path

@router.message(Command("check_progress"))
async def check_progress(message: Message):
    try:
        user_id = str(message.from_user.id)
        progress = data_manager.get_progress(user_id)
        
        if "error" in progress:
            if progress["error"] == "Профиль не найден":
                await message.answer("❌ Сначала создайте профиль с помощью /set_profile")
            else:
                await message.answer(f"❌ Ошибка: {progress['error']}")
            return
        
        # Расчет процентов выполнения целей
        water_percent = round((progress["water"]["consumed"] / progress["water"]["goal"]) * 100)
        calories_percent = round((progress["calories"]["consumed"] / progress["calories"]["goal"]) * 100)
        
        water_progress = "🌊 Вода:\n"
        water_progress += f"└ Выпито: {progress['water']['consumed']} мл из {progress['water']['goal']} мл ({water_percent}%)\n"
        if progress["water"]["remaining"] > 0:
            water_progress += f"└ Осталось: {progress['water']['remaining']} мл\n"
        else:
            water_progress += "└ ✅ Цель по воде выполнена!\n"
            
        food_log = ""
        if progress["food_log"]:
            food_log = "\n🍽 Приемы пищи сегодня:\n"
            for entry in progress["food_log"]:
                food_log += f"└ {entry['food']}: {entry['amount']}г ({round(entry['calories'])} ккал)\n"
                
        workout_log = ""
        if progress["workout_log"]:
            workout_log = "\n🏃‍♂️ Тренировки сегодня:\n"
            for entry in progress["workout_log"]:
                workout_log += f"└ {entry['type'].capitalize()}: {entry['duration']} мин ({entry['calories_burned']} ккал)\n"
        
        calories_progress = "\n🔥 Калории:\n"
        calories_progress += f"└ Потреблено: {progress['calories']['consumed']} ккал из {progress['calories']['goal']} ккал ({calories_percent}%)\n"
        calories_progress += f"└ Сожжено: {progress['calories']['burned']} ккал\n"
        
        # Расчет итогового баланса
        net_calories = progress['calories']['consumed'] - progress['calories']['burned']
        remaining_calories = progress['calories']['goal'] - net_calories
        
        if remaining_calories > 0:
            calories_progress += f"└ Можно еще: {remaining_calories} ккал\n"
        else:
            calories_progress += "└ ⚠️ Превышен дневной лимит калорий\n"
            
        message_text = (
            "📊 Прогресс на сегодня:\n\n" +
            water_progress + "\n" +
            calories_progress +
            food_log +
            workout_log
        )
        
        graph_path = await create_progress_graphs(user_id)
        
        # Отправляем текстовый отчет и графики
        await message.answer_photo(
            FSInputFile(graph_path),
            caption=message_text
        )
        
        # Удаляем временный файл с графиком
        os.remove(graph_path)
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при получении прогресса: {str(e)}")
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при получении прогресса: {str(e)}")