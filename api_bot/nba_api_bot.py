"""Телеграм-бот для просмотра статистики NBA."""

import os

import requests

import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне


from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from dotenv import load_dotenv

import logging



load_dotenv()




ENDPOINT = 'https://www.balldontlie.io/api/v1/'

ADMIN_ID = 2079808924 # Айди аккаунта в телеграм

BOT_TOKEN = 5371289148:AAHgpsuBitiw6T-U9KFt05IVDLoskbBAFys # Токен бота в телеграм





logging.basicConfig(level=logging.DEBUG, filename='main.log', filemod='w', format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'

response = requests.get(ENDPOINT)

response = response.json()




bot = telegram.Bot(token=BOT_TOKEN) # создание экземпляра бота

updater = Updater(token=BOT_TOKEN) # создание экземпляра для проверки входящих 

bot.send_message(CHAT_ID, text) # пример отправки сообщения



def say_hi(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Привет!')


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.from.first_name
    button = ReplyKeyboardMarkup([['Кнопка 1', 'Кнопка 2'], ['Кнопка 3', 'Кнопка 4']], resize_keyboard=True)
    context.bot.send_message(chat_id=chat.id, text='Спасибо, что включили меня {}!'.format(name), reply_markup=button)


updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi)) # Filters - обработчики типов сообщений

updater.start_polling(pool_interval=10.0)

updater.idle()



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
