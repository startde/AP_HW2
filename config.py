import os
from dotenv import load_dotenv
# Суперподробное логирование для отладки
import logging

# logging.basicConfig(level=logging.DEBUG)

# aiohttp_logger = logging.getLogger("aiohttp")
# aiohttp_logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загрузка переменных из .env файла
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
# CURRENCY_API_KEY = os.getenv("API_TOKEN")
# CURRENCY_API_URL = "https://api.apilayer.com/exchangerates_data/latest"

if not API_TOKEN:
    raise NameError