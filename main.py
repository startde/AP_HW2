import asyncio
from aiogram import Bot, Dispatcher
from config import API_TOKEN
from message_handlers import router
from config import logger

#Запуск бота
async def main():
    bot = Bot(token= API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router=router)
    
    logger.info("Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())