"""Телеграм-бот для просмотра статистики NBA."""
import logging
import os
import sys
import re

import requests
import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from models import player, team_min, statistics


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

cache_dict = {}
control_panel = {} # {'chat.id': {'search...': '...', 'statistics': '...'}, }


def answer_hub(update, context):
    text = update['message']['text']
    chat = update.effective_chat
    control_action = control_panel.get(chat.id)
    if text == 'В начало':
        control_panel[chat.id] = None
        return head_page(update, context)
    if control_action is not None:
        if control_action.get('statistics_season'):
            return statistics_season(update, context)
        if control_action.get('search_player'):
            return search_player(update, context)
        if control_action.get('player_id'):
            if text == 'Статистика по играм':
                return preview_statistics(update, context, False)
            if text == 'Статистика сезона':
                control_panel[chat.id]['statistics_season'] = True
                return preview_statistics(update, context)
    if text == 'Поиск игрока':
        return pre_search_player(update, context)
    if text == 'Команды':
        return view_teams(update, context)
    return head_page(update, context)


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = telegram.ReplyKeyboardMarkup(
        [['Поиск игрока', 'Поиск команды'], ['Команды', 'Кнопка 4']],
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
        [['Поиск игрока', 'Поиск команды'], ['Команды', 'Кнопка 4']],
        resize_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat.id,
        text='Чем я могу Вам помочь, {}?'.format(name),
        reply_markup=button
    )


def pre_search_player(update, context):
    chat = update.effective_chat
    flag = {'search_player': 'search_player'}
    control_panel[chat.id] = flag
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
    text = (update['message']['text']).rstrip()
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    if re.match(r'^[a-zA-Z ]+$', text) is None:
        return context.bot.send_message(
            chat_id=chat.id,
            text='Пожалуйста, введите запрос на латинице',
            reply_markup=button
        )
    text = '_'.join((text).split())
    response = requests.get(
        '{}/players?per_page=25&search={}'.format(ENDPOINT, text)
    )
    response = response.json()
    response_list = response.get('data')
    player_count = response.get('meta').get('total_count')
    if player_count == 0:     
        return context.bot.send_message(
            chat_id=chat.id,
            text='К сожалению ничего не найдено. Уточните запрос',
            reply_markup=button
        )
    if player_count > 25:      
        return context.bot.send_message(
            chat_id=chat.id,
            text=(
                'Пожалуйста, уточните поиск.\n'
                'Количество найденных игроков превышает 25!'
            ),
            reply_markup=button
        )
    if player_count > 1:
        list_name = [
            str(
                i['first_name']) + ' ' + str(i['last_name']
            ) for i in response_list
        ]
        return context.bot.send_message(
            chat_id=chat.id,
            text=(
                'Пожалуйста, уточните поиск - введите имя '
                'из предложенного списка:\n{}'.format('\n'.join(list_name))
            ),
            reply_markup=button
        )
    if response_list:
        response = response_list[0]
        player_id = response.get('id')
        control_panel[chat.id]['player_id'] = player_id
        f_n = response.get('first_name')
        l_n = response.get('last_name')
        result = player(response)
        info_for_photo = '{}_{}'.format(f_n, l_n)
        photo = requests.get(f'{ENDPOINT_PHOTO_SEARCH}{info_for_photo}')
        photo = photo.json()['results'][0]
        button = telegram.ReplyKeyboardMarkup(
            [['Статистика сезона', 'Статистика по играм'],
            ['В начало']],
            resize_keyboard=True
        )
        context.bot.send_photo(
            chat_id=chat.id, photo=photo, caption=result, reply_markup=button
        )
        control_panel[chat.id]['search_player'] = None


def view_teams(update, context):
    chat = update.effective_chat
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    if cache_dict.get('list_teams') is None:
        response = requests.get(
            f'{ENDPOINT}/teams'
        )
        response = response.json()
        response_list = response.get('data')
        teams_count = response.get('meta').get('total_count')
        if teams_count and response_list:
            list_teams = [team_min(i) for i in response_list]
            cache_dict['list_teams'] = list_teams
    list_teams = cache_dict.get('list_teams')
    return context.bot.send_message(
        chat_id=chat.id,
        text=(
            'Список текущих команд NBA:\n\n{}'.format('\n'.join(list_teams))
        ),
        reply_markup=button
    )


def preview_statistics(update, context, season=True):
    chat = update.effective_chat
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    if season:
        text = (
            'Введите сезон, в течение которого '
            'Вам интересна статистика игрока.\n'
            'К примеру, если требуется статистика игрока за сезон 2016-2017 '
            'вводить нужно "2016".\n'
            'Запрос должен содержать только четыре цифры.'
        )
    context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=button
    )


def statistics_game(update, context):
    pass


def statistics_season(update, context):
    chat = update.effective_chat
    text = (update['message']['text']).rstrip()
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    if re.match(r'^[\d+]{4}$', text) is None:
        return context.bot.send_message(
            chat_id=chat.id,
            text='Пожалуйста, введите 4 цифры года',
            reply_markup=button
        )
    player_id = control_panel.get(chat.id).get('player_id')
    response = requests.get(
        '{}/season_averages?season={}&player_ids[]={}'.format(
            ENDPOINT, text, player_id
        )
    )
    response = response.json()
    response_list = response.get('data')
    if response_list:
        response = response_list[0]
        result = statistics(response)
        response = requests.get(
            '{}/players/{}'.format(ENDPOINT, player_id)
        )
        response = response.json()
        f_n = response.get('first_name')
        l_n = response.get('last_name')
        text = f'Статистика игрока {f_n} {l_n}:\n{result}'
        button = telegram.ReplyKeyboardMarkup(
            [['Выбрать другой сезон', 'Статистика по играм'],
            ['В начало']],
            resize_keyboard=True
        )
        return context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=button
        )
    return context.bot.send_message(
        chat_id=chat.id,
        text='Статистики за данный период не найдено',
        reply_markup=button
    )    


updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler
updater.dispatcher.add_handler(MessageHandler(Filters.text, answer_hub)) # Filters - обработчики типов сообщений
updater.start_polling(poll_interval=10.0)
updater.idle()
