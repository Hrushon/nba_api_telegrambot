"""Телеграм-бот для просмотра статистики NBA."""
import logging
import os
import sys
import re

import requests
import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from models import player, statistics


load_dotenv()

ENDPOINT = 'https://www.balldontlie.io/api/v1/'
ENDPOINT_PHOTO_SEARCH = 'https://imsea.herokuapp.com/api/1?q=nba_'

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


control_panel = {} # {'chat.id': 'search...', }


def say_hi(update, context):
    text = update['message']['text']
    chat = update.effective_chat
    if text == 'В начало':
        control_panel[chat.id] = None
        return head_page(update, context)
    control_action = control_panel.get(chat.id)
    if control_action is not None:
        if control_action == 'search_player':
            return search_player(update, context)
    if text == 'Поиск игрока':
        return pre_search_player(update, context)
    context.bot.send_message(chat_id=chat.id, text='Привет!')


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = telegram.ReplyKeyboardMarkup(
        [['Поиск игрока', 'Поиск команды'], ['Кнопка 3', 'Кнопка 4']],
        resize_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat.id,
        text='Спасибо, что включили меня, {}!'.format(name),
        reply_markup=button
    )


def head_page(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = telegram.ReplyKeyboardMarkup(
        [['Поиск игрока', 'Поиск команды'], ['Кнопка 3', 'Кнопка 4']],
        resize_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat.id,
        text='Чем я могу Вам помочь, {}?'.format(name),
        reply_markup=button
    )


def pre_search_player(update, context):
    chat = update.effective_chat
    control_panel[chat.id] = 'search_player'
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    text = (
        'Введите имя игрока, которого Вы хотите найти. '
        'Запрос должен быть на латинице.'
    )
    context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=button
    )


def search_player(update, context):
    chat = update.effective_chat
    text = update['message']['text']
    if not re.match(r'^[a-zA-Z]+$', text):
        button = telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        )            
        return context.bot.send_message(
            chat_id=chat.id,
            text='Пожалуйста, введите запрос на латинице',
            reply_markup=button
        )        
    text = '_'.join((text).split())
    response = requests.get('{}/players?per_page=100&search={}'.format(ENDPOINT, text))
    response = response.json()
    if response.get('meta').get('total_count') == 0:
        button = telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        )            
        return context.bot.send_message(
            chat_id=chat.id,
            text='К сожалению ничего не найдено. Уточните запрос',
            reply_markup=button
        )
    if response.get('meta').get('total_count') > 100:
        button = telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        )            
        return context.bot.send_message(
            chat_id=chat.id,
            text='Пожалуйста, уточните поиск.\nКоличество найденных игроков превышает 100!',
            reply_markup=button
        )
    if response.get('meta').get('total_count') > 1:
        list_name = []
        for i in response.get('data'):
            list_name.append('{} {}'.format(i.get('first_name'), i.get('last_name')))
        button = telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        )            
        return context.bot.send_message(
            chat_id=chat.id,
            text='Пожалуйста, уточните поиск - введите имя из предложенного списка:\n{}'.format('\n'.join(list_name)),
            reply_markup=button
        )
    response = response['data'][0]
    f_n = response.get('first_name')
    l_n = response.get('last_name')
    result = player(response)
    info_for_photo = '{}_{}'.format(f_n, l_n)
    photo = requests.get(f'{ENDPOINT_PHOTO_SEARCH}{info_for_photo}')
    photo = photo.json()['results'][0]
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    context.bot.send_photo(chat_id=chat.id, photo=photo, caption=result, reply_markup=button)
    control_panel[chat.id] = None

# response = requests.get(f'{ENDPOINT}/players/?search=lebron')
# response = response.json()['data'][0]
# f_n = response.get('first_name')
# l_n = response.get('last_name')
# info_for_photo = f'{f_n}_{l_n}'
# text = player(response)
# photo = requests.get(f'{ENDPOINT_PHOTO_SEARCH}{info_for_photo}')
# photo = photo.json()['results'][0]
# bot.send_photo(ADMIN_ID, photo, caption=text)

# response = requests.get(f'{ENDPOINT}/season_averages?season=2020&player_ids[]=237')
# response = response.json()['data'][0]
# text = statistics(response)
# response = requests.get(f'{ENDPOINT}/players/237')
# response = response.json()
# f_n = response.get('first_name')
# l_n = response.get('last_name')
# name = 'Статистика игрока: {} {}.\n'.format(f_n, l_n)
# bot.send_message(ADMIN_ID, name + text)

updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler
updater.dispatcher.add_handler(MessageHandler(Filters.text, say_hi)) # Filters - обработчики типов сообщений
updater.start_polling(poll_interval=10.0)
updater.idle()
