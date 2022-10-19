"""Телеграм-бот для просмотра статистики NBA."""
import logging
import os
import sys
from urllib import response

import requests
import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from models import player


load_dotenv()

ENDPOINT = 'https://www.balldontlie.io/api/v1/'
ENDPOINT_PHOTO_SEARCH = 'https://imsea.herokuapp.com/api/1?q='

ADMIN_ID = os.getenv('ADMIN_ID') # Айди аккаунта в телеграм
BOT_TOKEN = os.getenv('BOT_TOKEN') # Токен бота в телеграм


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)




bot = telegram.Bot(token=BOT_TOKEN) # создание экземпляра бота
updater = Updater(token=BOT_TOKEN) # создание экземпляра для проверки входящих 
# bot.send_message(CHAT_ID, text) # пример отправки сообщения


def say_hi(update, context):
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id, text='Привет!')


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = telegram.ReplyKeyboardMarkup([['Кнопка 1', 'Кнопка 2'], ['Кнопка 3', 'Кнопка 4']], resize_keyboard=True)
    context.bot.send_message(chat_id=chat.id, text='Спасибо, что включили меня {}!'.format(name), reply_markup=button)

response = requests.get(f'{ENDPOINT}/players/?search=lebron')
response = response.json()['data'][0]
f_n = response.get('first_name')
l_n = response.get('last_name')
info_for_photo = f'{f_n}_{l_n}'
text = player(response)
photo = requests.get(f'{ENDPOINT_PHOTO_SEARCH}{info_for_photo}')
photo = photo.json()['results'][0]
bot.send_photo(ADMIN_ID, photo, caption=text)



updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi)) # Filters - обработчики типов сообщений
updater.start_polling(poll_interval=10.0)
updater.idle()
