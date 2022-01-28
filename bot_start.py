import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv('x-rapidapi-key')
BOT = telebot.TeleBot(TOKEN)