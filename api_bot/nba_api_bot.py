"""Телеграм-бот для просмотра статистики NBA."""
import requests
import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне


ENDPOINT = 'https://www.balldontlie.io/api/v1/'
CHAT_ID = 2079808924 # Айди аккаунта в телеграм
BOT_TOKEN = 5371289148:AAHgpsuBitiw6T-U9KFt05IVDLoskbBAFys # Токен бота в телеграм

response = requests.get(ENDPOINT)
response = response.json()

bot = telegram.Bot(token=BOT_TOKEN) # создание экземпляра бота
updater = tekegram.ext.Updater(token=BOT_TOKEN) # создание экземпляра для проверки входящих 
bot.send_message(CHAT_ID, text) # пример отправки сообщения
