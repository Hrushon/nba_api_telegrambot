"""Телеграм-бот для просмотра статистики NBA."""
import requests


ENDPOINT = 'https://www.balldontlie.io/api/v1/'
CHAT_ID = 2079808924 # Айди аккаунта в телеграм
BOT_TOKEN = 5371289148:AAHgpsuBitiw6T-U9KFt05IVDLoskbBAFys # Токен бота в телеграм

response = requests.get(ENDPOINT)
response = response.json()
