"""Телеграм-бот для просмотра статистики NBA."""
import logging
import os
import sys

import requests
import telegram
from http import HTTPStatus
from datetime import datetime

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from constants import VIEW_GAMES, VIEW_STATIX
from models import game_view, player, team_min, statistics, statistics_per_game
from validator import validator


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


def answer_hub(update, context):
    text = update['message']['text']
    if text == 'В начало':
        context.user_data.clear()
        return head_page(update, context, False)
    if text == 'Назад':
        return back_to_the_future(update, context)
    if text == 'Следующие игры' or text == 'Предыдущие игры':
        return flipp_pages(update, context)
    if text == 'Статистика по играм' or context.user_data.get(
        'statistics'
    ) is not None:
        return preview_statistics(update, context)
    if text in (
        'Статистика сезона', 'Выбор другого сезона'
    ) or context.user_data.get('average') is not None:
        return statistics_season(update, context)
    if text == 'Игроки и статистика' or context.user_data.get(
        'player'
    ) is not None:
        return search_player(update, context)
    if text == 'Команды':
        return view_teams(update, context)
    if text == 'Игры' or context.user_data.get('games') is not None:
        return preview_games(update, context)
    return head_page(update, context, False)


def head_page(update, context, start=True):
    chat = update.effective_chat
    name = update.message.chat.first_name
    text = f'Чем я могу Вам помочь, {name}?'
    if start:
        text = f'Спасибо, что включили меня, {name}!'
    button = telegram.ReplyKeyboardMarkup(
        [['Игры'], ['Команды'], ['Игроки и статистика']],
        resize_keyboard=True
    )
    context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=button
    )


def back_to_the_future(update, context):
    statictics_flag = context.user_data.get('statistics')
    games_flag = context.user_data.get('games')

    if statictics_flag is not None:
        count = len(statictics_flag)
        if count != 0:
            statictics_flag.pop()
        else:
            context.user_data.pop('statistics')
        return preview_statistics(update, context)
    if games_flag is not None:
        count = len(games_flag)
        if count != 0:
            games_flag.pop()
        else:
            context.user_data.pop('games')
        return preview_games(update, context)

    return head_page(update, context)


def search_player(update, context):
    chat = update.effective_chat
    answer = (update['message']['text']).rstrip()
    flag_dict = context.user_data.get('player')
    text = 'Что-то пошло не так!'

    if flag_dict is not None:
        if validator(update, context):
            answer = '_'.join((answer).split())
            response = requests.get(
                f'{ENDPOINT}players?per_page=25&search={answer}'
            )
            response = response.json()
            response_list = response.get('data')
            player_count = response.get('meta').get('total_count')
            if player_count == 0:
                text='К сожалению ничего не найдено. Уточните запрос'
            elif player_count > 25:
                text=(
                    'Пожалуйста, уточните поиск.\n'
                    'Количество найденных игроков превышает *25*!'
                )
            elif player_count > 1:
                list_name = [
                    str(i['first_name']) + ' ' + str(i['last_name'])
                    for i in response_list
                ]
                text=(
                    'Уточните поиск - введите имя '
                    'из предложенного списка:\n_{}_'.format('\n'.join(list_name))
                )
            elif response_list:
                response = response_list[0]
                player_id = response.get('id')
                first_name = response.get('first_name')
                last_name = response.get('last_name')
                context.user_data.get('player').append(player_id)
                context.user_data.get('player').append(first_name)
                context.user_data.get('player').append(last_name)
                result = player(response)
                info_for_photo = '{}_{}'.format(first_name, last_name)
                photo = requests.get(f'{ENDPOINT_PHOTO_SEARCH}{info_for_photo}')
                button = telegram.ReplyKeyboardMarkup(
                    [
                        ['Статистика сезона', 'Статистика по играм'],
                        ['В начало']
                    ],
                    resize_keyboard=True
                )
                if photo.status_code == HTTPStatus.OK:
                    photo = photo.json()['results'][0]
                    return context.bot.send_photo(
                        chat_id=chat.id,
                        photo=photo,
                        caption=result,
                        reply_markup=button,
                        parse_mode='Markdown'
                    )
                return context.bot.send_message(
                    chat_id=chat.id,
                    text=result,
                    reply_markup=button,
                    parse_mode='Markdown'
                )

        else:
            text = ('Попробуйте уточнить запрос. Ничего не найдено.\n'
                   'Убедитесь что Вы ввели верный запрос на латинице')

    else:
        text = (
            'Введите имя игрока, которого Вы хотите найти. '
            'Запрос должен быть на латинице.'
        )
        context.user_data['player'] = []

    return context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        ),
        parse_mode = 'Markdown'
    )


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
        reply_markup=button,
        parse_mode='Markdown'
    )


def preview_statistics(update, context):
    chat = update.effective_chat
    answer = (update['message']['text']).rstrip()
    flag_dict = context.user_data.get('statistics')
    button = [['Назад'], ['В начало']]
    text = ''

    if flag_dict is not None:
        count = len(flag_dict)

        if answer == VIEW_STATIX.get(count).get('answer')[0]:
            text = VIEW_STATIX.get(count).get('additional')
            if text is None:
                context.user_data.get('statistics').append(True)

        elif answer == VIEW_STATIX.get(count).get('answer')[1]:
            context.user_data.get('statistics').append(False)

        elif validator(update, context):
            context.user_data.get('statistics').append(answer)
            if len(context.user_data.get('statistics')) in (1, 3, 5):
                return view_statistics(update, context)

        else:
            text = 'Попробуйте уточнить запрос. Ничего не найдено.'

        if not text or answer == 'Назад':
            text = VIEW_STATIX.get(count).get('text')
            button = VIEW_STATIX.get(count).get('button')

    else:
        button = [['Да', 'Нет'], ['В начало']]
        text = (
            'Вы знаете ID игры и хотите посмотреть детали ее статистики?\n'
            '_ID можно узнать в разделе "Игры"_'
        )
        context.user_data['statistics'] = []

    return context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        ),
        parse_mode = 'Markdown'
    )


def view_statistics(update, context):
    chat = update.effective_chat
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    if context.user_data.get('player') is not None:
        player_id = context.user_data.get('player')[0]
        first_name = context.user_data.get('player')[1]
        last_name = context.user_data.get('player')[2]
    user_data = context.user_data.get('statistics')
    game_id, playoff, season = user_data[0], user_data[1], user_data[2]
    final_url = (f'{ENDPOINT}stats?player_ids[]={player_id}'
                 f'&per_page=5&postseason={playoff}')
    
    if game_id:
        final_url += f'&game_ids[]={game_id}'
    if season:
        final_url += f'&seasons[]={season}'


    if not isinstance(season, str):
        if not user_data[3]:
            user_data = (user_data[4]).split(' ')
            start_date, end_date = *user_data,
            start_date = '-'.join(reversed(start_date.split('-')))
            end_date = '-'.join(reversed(end_date.split('-')))
            final_url += f'&start_date={start_date}&end_date={end_date}'
        else:
            date = user_data[4]
            final_url += f'&dates[]={date}'

    response = requests.get(final_url)
    final_url = response.url
    response = response.json()
    response_list = response.get('data')
    games_count = response.get('meta').get('total_count')
    pages_count = response.get('meta').get('total_pages')
    if response_list and games_count:
        result = [statistics_per_game(i) for i in response_list]
        if pages_count > 1:
            page = pages_count
            button = telegram.ReplyKeyboardMarkup(
                [['Следующие игры'],
                ['В начало']],
                resize_keyboard=True
            )
            context.user_data['current_endpoint'] = final_url
            context.user_data['current_page'] = page
            final_url += f'&page={page}'
            response = requests.get(final_url)
            response = response.json()
            response_list = response.get('data')
            result = [statistics_per_game(i) for i in response_list]

        text = ('Статистика игрока *{} {}* по играм:\n\n'
                'Количество игр в выборке: *{}*\n\n{}').format(
            first_name, last_name, games_count, '\n'.join(reversed(result))
        )
        return context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=button,
            parse_mode='Markdown'
        )
    return context.bot.send_message(
        chat_id=chat.id,
        text='Статистики за данный период не найдено',
        reply_markup=button
    )


def statistics_season(update, context):
    chat = update.effective_chat
    button = [['В начало']]
    answer = (update['message']['text']).rstrip()
    flag_dict = context.user_data.get('average')
    if context.user_data.get('player') is not None:
        player_id = context.user_data.get('player')[0]
        first_name = context.user_data.get('player')[1]
        last_name = context.user_data.get('player')[2]

    if flag_dict is not None and answer != 'Выбрать другой сезон':
        if validator(update, context):
            response = requests.get(
                '{}season_averages?season={}&player_ids[]={}'.format(
                    ENDPOINT, answer, player_id
                )
            )
            response = response.json()
            response_list = response.get('data')
            if response_list:
                response = response_list[0]
                result = statistics(response)
                text = f'Статистика игрока *{first_name} {last_name}*:\n\n{result}'
                button = telegram.ReplyKeyboardMarkup(
                    [['Выбрать другой сезон', 'Статистика по играм'],
                    ['В начало']],
                    resize_keyboard=True
                )
                return context.bot.send_message(
                    chat_id=chat.id,
                    text=text,
                    reply_markup=button,
                    parse_mode='Markdown'
                )
        else:
            text = ('Убедитесь что Вы ввели верный запрос')

    else:
        text = (
            'Введите сезон, в пределах которого '
            'Вас интересует статистика игрока.\n'
            'К примеру, если требуется статистика игрока '
            'за сезон 2016-2017 ввести нужно - "*2016*".\n'
            'Запрос должен содержать только четыре цифры.'
        )
        context.user_data['average'] = []

    return context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        ),
        parse_mode = 'Markdown'
    )


def preview_games(update, context):
    chat = update.effective_chat
    answer = (update['message']['text']).rstrip()
    flag_dict = context.user_data.get('games')
    button = [['Назад'], ['В начало']]
    text = ''

    if flag_dict is not None:
        count = len(flag_dict)

        if answer == VIEW_GAMES.get(count).get('answer')[0]:
            text = VIEW_GAMES.get(count).get('additional')
            if text is None:
                context.user_data.get('games').append(True)

        elif answer == VIEW_GAMES.get(count).get('answer')[1]:
            context.user_data.get('games').append(False)

        elif validator(update, context):
            context.user_data.get('games').append(answer)
            if len(context.user_data.get('games')) in (3, 5):
                return view_games(update, context)

        else:
            text = ('Попробуйте уточнить запрос. '
                   'По Вашему запросу ничего не найдено.')

        if not text or answer == 'Назад':
            text = VIEW_GAMES.get(count).get('text')
            button = VIEW_GAMES.get(count).get('button')


    else:
        button = [['Только плей-офф'], ['Все игры'], ['В начало']]
        text = 'Выберите тип игр'
        context.user_data['games'] = []

    return context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        ),
        parse_mode = 'Markdown'
    )


def view_games(update, context):
    chat = update.effective_chat
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    user_data = context.user_data.get('games')
    playoff, team_id, season = user_data[0], user_data[1], user_data[2]
    final_url = f'{ENDPOINT}games?per_page=5&postseason={playoff}'
    
    if team_id:
        final_url += f'&team_ids[]={team_id}'
    if season:
        final_url += f'&seasons[]={season}'


    if not isinstance(season, str):
        if not user_data[3]:
            user_data = (user_data[4]).split(' ')
            start_date, end_date = *user_data,
            start_date = '-'.join(reversed(start_date.split('-')))
            end_date = '-'.join(reversed(end_date.split('-')))
            final_url += f'&start_date={start_date}&end_date={end_date}'
        else:
            date = user_data[4]
            final_url += f'&dates[]={date}'

    response = requests.get(final_url)
    final_url = response.url
    response = response.json()
    response_list = response.get('data')
    games_count = response.get('meta').get('total_count')
    pages_count = response.get('meta').get('total_pages')
    if games_count and response_list:
        result = [game_view(i) for i in response_list]
        if pages_count > 1:
            page = pages_count
            button = telegram.ReplyKeyboardMarkup(
                [['Следующие игры'],
                ['В начало']],
                resize_keyboard=True
            )
            context.user_data['current_endpoint'] = final_url
            context.user_data['current_page'] = page
            final_url += f'&page={page}'
            response = requests.get(final_url)
            response = response.json()
            response_list = response.get('data')
            result = [game_view(i) for i in response_list]

        text = ('Количество игр в выборке: *{}*\nСписок игр:\n{}'.format(
                games_count, '\n'.join(reversed(result))
        ))
        return context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=button,
            parse_mode='Markdown'
        )
    return context.bot.send_message(
        chat_id=chat.id,
        text='Игр за данный период не найдено',
        reply_markup=button
    )


def flipp_pages(update, context):
    text = 'Что-то не так'
    chat = update.effective_chat
    answer = (update['message']['text']).rstrip()
    button = [['Предыдущие игры'], ['Следующие игры'], ['В начало']]
    final_url = context.user_data.get('current_endpoint')
    current_page = context.user_data.get('current_page')
    if answer == 'Следующие игры':
        page = current_page - 1
    else:
        page = current_page + 1
    context.user_data['current_page'] = page
    params = {'page': page}
    response = requests.get(final_url, params=params)
    response = response.json()
    response_list = response.get('data')
    if response_list:
        pages_count = response.get('meta').get('total_pages')
        if page == pages_count:
            button = [['Следующие игры'], ['В начало']]
        if page == 1:
            button = [['Предыдущие игры'], ['В начало']]
        games_count = response.get('meta').get('total_count')
        if context.user_data.get('statistics'):
            result = [statistics_per_game(i) for i in response_list]
            first_name = context.user_data.get('player')[1]
            last_name = context.user_data.get('player')[2]
            text = ('Статистика игрока *{} {}* по играм:\n\n'
                    'Количество игр в выборке: *{}*\n\n{}').format(
                first_name, last_name, games_count,
                '\n'.join(reversed(result))
            )
        elif context.user_data.get('games'):
            result = [game_view(i) for i in response_list]
            text = ('Количество игр в выборке: *{}*\nСписок игр:\n{}'.format(
                games_count, '\n'.join(reversed(result))
            ))
 
    return context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        ),
        parse_mode='Markdown'
    )


updater.dispatcher.add_handler(CommandHandler('start', head_page))
updater.dispatcher.add_handler(MessageHandler(Filters.all, answer_hub))
updater.start_polling(poll_interval=5.0)
updater.idle()
