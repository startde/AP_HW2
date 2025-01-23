from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums.parse_mode import ParseMode
from data_manager import DataManager

router_create_profile = Router()
data_manager=DataManager()

class CreateProfile(StatesGroup):
    getHeight = State()
    getAge = State()
    getActivity = State()
    getCity = State()
    final = State()

@router_create_profile.message(Command('set_profile'))
async def get_weight(message: Message, state: FSMContext):
    await message.answer(text="Настроим профиль! Введите ваш вес (в килограммах)")
    await state.set_state(CreateProfile.getHeight)

@router_create_profile.message(CreateProfile.getHeight)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer(text="Отлично! Введите ваш рост (в сантиметрах)")
    await state.set_state(CreateProfile.getAge)

@router_create_profile.message(CreateProfile.getAge)
async def get_age(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer(text="Супер! Введите ваш возраст")
    await state.set_state(CreateProfile.getActivity)

@router_create_profile.message(CreateProfile.getActivity)
async def get_activity(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer(text="Осталось совсем немного! Сколько минут активности у вас в день?")
    await state.set_state(CreateProfile.getCity)

@router_create_profile.message(CreateProfile.getCity)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.answer(text="В каком городе вы находитесь (напиши по английски)?")
    await state.set_state(CreateProfile.final)

@router_create_profile.message(CreateProfile.final)
async def get_final(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    profile_data = await state.get_data()
    await message.answer(text=f"Это данные твоего профиля:\n"
                         f"<b>Вес:</b> {profile_data['weight']}\n"
                         f"<b>Рост:</b> {profile_data['height']}\n"
                         f"<b>Возраст:</b> {profile_data['age']}\n"
                         f"<b>Количество минут активности в день:</b> {profile_data['activity']}\n"
                         f"<b>Город:</b> {profile_data['city']}",
                         parse_mode=ParseMode.HTML
                         )
    user_id = str(message.from_user.id)
    profile = data_manager.create_profile(user_id, profile_data)
    print(profile)
    await state.clear()