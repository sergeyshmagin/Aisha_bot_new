import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = AsyncTeleBot(TELEGRAM_TOKEN) 