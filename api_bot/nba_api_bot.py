"""Телеграм-бот для просмотра статистики NBA."""
import requests


ENDPOINT = 'https://www.balldontlie.io/api/v1/'
CHAT_ID = 2079808924 # Айди аккаунта в телеграм
BOT_TOKEN = 5562312403:AAFkjYcAtP5Rg0hsXpQtvh9UriqwfrP2KO8 # Токен бота в телеграм

response = requests.get(ENDPOINT)
response = response.json()
