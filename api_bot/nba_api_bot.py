"""Телеграм-бот для просмотра статистики NBA."""
import logging
import os
import sys
import re

import requests
import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from models import player, team_min, statistics, statistics_per_game


load_dotenv()

ENDPOINT = 'https://www.balldontlie.io/api/v1/'
ENDPOINT_PHOTO_SEARCH = 'https://imsea.herokuapp.com/api/1?q=nba_'

ADMIN_ID = os.getenv('ADMIN_ID') # Айди аккаунта в телеграм
BOT_TOKEN = os.getenv('BOT_TOKEN') # Токен бота в телеграм

STATX_GAME = {
    'gameid': [
        '^[\d]+$', 
        '{ENDPOINT}/stats?player_ids[]={player_id}&game_ids={text}'
    ],
    'allgame_period': [(
        '^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d) '
        '(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d)$'
    ), (
        '{ENDPOINT}/stats?player_ids[]={player_id}&start_date={start_date}'
        '&end_date={end_date}&per_page=5&page={page}'
    )],
    'playoff_period': [(
        '^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d) '
        '(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d)$'
    ), (
        '{ENDPOINT}/stats?player_ids[]={player_id}&start_date={start_date}'
        '&end_date={end_date}&postseason=true&per_page=5&page={page}'
    )],
    'allgame_season': ['^[\d+]{4}$', (
        '{ENDPOINT}/stats?player_ids[]={player_id}&seasons[]={text}'
        '&per_page=5&page={page}'
    )],
    'playoff_season': ['^[\d+]{4}$', (
        '{ENDPOINT}/stats?player_ids[]={player_id}&seasons[]={text}'
        '&postseason=true&per_page=5&page={page}'
    )]
}

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
control_panel = {} # {'chat.id': {'search...': '...', 'statistics': '...', }, }


def answer_hub(update, context):
    text = update['message']['text']
    chat = update.effective_chat
    control_action = control_panel.get(chat.id)
    if text == 'В начало':
        control_panel[chat.id] = None
        return head_page(update, context)
    if control_action is not None:
        if text == 'Следующие игры' or text == 'Предыдущие игры':
            return flipp_pages(update, context)
        if control_action.get('statistics'):
            if control_action.get('statistics') == 'season':
                return statistics_season(update, context)
            if control_action.get('statistics') == 'game':
                if text == 'Конкретная игра (по ID игры)':
                    control_panel[chat.id]['statistic_index'] = 'gameid'
                    return preview_statistics(
                        update, context, season=False, gameid=True
                    )
                if text == 'Все игры за определенный период':
                    control_panel[chat.id]['statistic_index'] = 'allgame_period'
                    return preview_statistics(
                        update, context, season=False, allgame_period=True
                    )
                if text == 'Игры плей-офф за определенный период':
                    control_panel[chat.id]['statistic_index'] = 'playoff_period'
                    return preview_statistics(
                        update, context, season=False, playoff_period=True
                    )
                if text == 'Все игры сезона':
                    control_panel[chat.id]['statistic_index'] = 'allgame_season'
                    return preview_statistics(
                        update, context, season=False, allgame_season=True
                    )
                if text == 'Игры плей-офф сезона':
                    control_panel[chat.id]['statistic_index'] = 'playoff_season'
                    return preview_statistics(
                        update, context, season=False, playoff_season=True
                    )
            if control_action.get('statistics') == 'game_go':
                return statistics_game(update, context)
        if control_action.get('search_player'):
            return search_player(update, context)
        if control_action.get('player_id'):
            if text == 'Поигровая статистика':
                control_panel[chat.id]['statistics'] = 'game'
                return preview_statistics(update, context, season=False)
            if text == 'Статистика сезона':
                control_panel[chat.id]['statistics'] = 'season'
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
                'Количество найденных игроков превышает *25*!'
            ),
            reply_markup=button,
            parse_mode='Markdown'
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
                'из предложенного списка:\n_{}_'.format('\n'.join(list_name))
            ),
            reply_markup=button,
            parse_mode='Markdown'
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
            [['Статистика сезона', 'Поигровая статистика'],
            ['В начало']],
            resize_keyboard=True
        )
        context.bot.send_photo(
            chat_id=chat.id,
            photo=photo,
            caption=result,
            reply_markup=button,
            parse_mode='Markdown'
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
        reply_markup=button,
        parse_mode='Markdown'
    )


def preview_statistics(
    update, context,
    season=True, gameid=False,
    allgame_period=False, playoff_period=False,
    allgame_season=False, playoff_season=False
):
    chat = update.effective_chat
    button = telegram.ReplyKeyboardMarkup(
        [['Конкретная игра (по ID игры)'],
        ['Все игры за определенный период', 'Игры плей-офф за определенный период'],
        ['Все игры сезона', 'Игры плей-офф сезона'],
        ['В начало']],
        resize_keyboard=True
    )
    text = (
        'Какая статистика игрока Вас интересует?'
    )
    if season:
        button = telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        )
        text = (
            'Введите сезон, в пределах которого '
            'Вас интересует статистика игрока.\n'
            'К примеру, если требуется статистика игрока за сезон 2016-2017 '
            'ввести нужно - "*2016*".\n'
            'Запрос должен содержать только четыре цифры.'
        )
    if gameid:
        button = telegram.ReplyKeyboardMarkup(
            [['Все игры за определенный период', 'Игры плей-офф за определенный период'],
            ['Все игры сезона', 'Игры плей-офф сезона'],
            ['В начало']],
            resize_keyboard=True
        )
        text = (
            'Введите ID игры.\n'
            'Только цифры.'
        )
        control_panel[chat.id]['statistics'] = 'game_go'
    if allgame_period:
        button = telegram.ReplyKeyboardMarkup(
            [['Конкретная игра (по ID игры)', 'Игры плей-офф за определенный период'],
            ['Все игры сезона', 'Игры плей-офф сезона'],
            ['В начало']],
            resize_keyboard=True
        )
        text = (
            'Ограничьте период в следующем формате:\n'
            'дд-мм-гггг дд-мм-гггг\n'
            'К примеру, если Вас интересует период с 1 января 2019 года '
            'по 1 марта 2019 года необходимо ввести следующее:\n'
            '*01-01-2019 01-03-2019*\n'
            'Будьте внимательны при вводе даты.'
        )
        control_panel[chat.id]['statistics'] = 'game_go'
    if playoff_period:
        button = telegram.ReplyKeyboardMarkup(
            [['Конкретная игра (по ID игры)', 'Все игры за определенный период'],
            ['Все игры сезона', 'Игры плей-офф сезона'],
            ['В начало']],
            resize_keyboard=True
        )
        text = (
            'Ограничьте период в следующем формате:\n'
            '_дд-мм-гггг дд-мм-гггг_\n'
            'К примеру, если Вас интересует период с 1 января 2019 года '
            'по 1 марта 2019 года необходимо ввести следующее:\n'
            '*01-01-2019 01-03-2019*\n'
            'Будьте внимательны при вводе дат.'
        )
        control_panel[chat.id]['statistics'] = 'game_go'
    if allgame_season:
        button = telegram.ReplyKeyboardMarkup(
            [['Конкретная игра (по ID игры)', 'Все игры за определенный период'],
            ['Игры плей-офф за определенный период', 'Игры плей-офф сезона'],
            ['В начало']],
            resize_keyboard=True
        )
        text = (
            'Введите сезон, в пределах которого '
            'Вас интересует статистика игрока.\n'
            'К примеру, если требуется статистика игрока за сезон 2016-2017 '
            'ввести нужно - "*2016*".\n'
            'Запрос должен содержать только четыре цифры.'
        )
        control_panel[chat.id]['statistics'] = 'game_go'
    if playoff_season:
        button = telegram.ReplyKeyboardMarkup(
            [['Конкретная игра (по ID игры)', 'Все игры за определенный период'],
            ['Игры плей-офф за определенный период', 'Все игры сезона'],
            ['В начало']],
            resize_keyboard=True
        )
        text = (
            'Введите сезон, в пределах которого '
            'Вас интересует статистика игрока.\n'
            'К примеру, если требуется статистика игрока '
            'за плей-офф сезона 2016-2017 '
            'ввести нужно - "*2016*".\n'
            'Запрос должен содержать только четыре цифры.'
        )
        control_panel[chat.id]['statistics'] = 'game_go'
    context.bot.send_message(
        chat_id=chat.id,
        text=text,
        reply_markup=button,
        parse_mode = 'Markdown'
    )


def statistics_game(update, context):
    chat = update.effective_chat
    text = (update['message']['text']).rstrip()
    button = telegram.ReplyKeyboardMarkup(
        [['В начало']],
        resize_keyboard=True
    )
    type_statistics = control_panel.get(chat.id).get('statistic_index')
    etalon = STATX_GAME.get(type_statistics)[0]
    if re.match(rf'{etalon}', text) is None:
        return context.bot.send_message(
            chat_id=chat.id,
            text=(
                'Ошибка при обработке данных.\n'
                'Пожалуйста, проверьте правильность ввода данных.'
            ),
            reply_markup=button
        )
    page, start_date, end_date = 0, 0, 0
    if ' ' in text:
        start_date=text.split()[0]
        end_date=text.split()[1]
    player_id = control_panel.get(chat.id).get('player_id')
    custom_url = STATX_GAME.get(type_statistics)[1]
    response = requests.get(custom_url.format(
        ENDPOINT=ENDPOINT, player_id=player_id,
        text=text, start_date=start_date,
        end_date=end_date, page=page
    ))
    final_url = response.url
    response = response.json()
    response_list = response.get('data')
    if response_list:
        button = telegram.ReplyKeyboardMarkup(
            [['Конкретная игра (по ID игры)'],
            ['Все игры за определенный период', 'Игры плей-офф за определенный период'],
            ['Все игры сезона', 'Игры плей-офф сезона'],
            ['В начало']],
            resize_keyboard=True
        )
        # control_panel[chat.id]['statistics'] = 'game'
        games_count = response.get('meta').get('total_count')
        pages_count = response.get('meta').get('total_pages')
        current_page = response.get('meta').get('current_page')
        per_page = response.get('meta').get('per_page')
        response = response_list[0]
        f_n = response.get('player').get('first_name')
        l_n = response.get('player').get('last_name')
        result = statistics_per_game(response)
        if pages_count > 1:
            button = telegram.ReplyKeyboardMarkup(
                [['Следующие игры'],
                ['В начало']],
                resize_keyboard=True
            )
            page = pages_count
            control_panel[chat.id]['endpoint'] = final_url
            control_panel[chat.id]['current_page'] = page
            response = requests.get(custom_url.format(
                ENDPOINT=ENDPOINT, player_id=player_id,
                text=text, start_date=start_date,
                end_date=end_date, page=page
            ))
            response = response.json()
            response_list = response.get('data')
            result = [statistics_per_game(i) for i in response_list]
        text = ('Статистика игрока *{} {}* по играм:\n\n'
                'Количество игр в выборке: *{}*\n\n{}').format(
            f_n, l_n, games_count, '\n'.join(reversed(result))
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
        text = f'Статистика игрока *{f_n} {l_n}*:\n{result}'
        button = telegram.ReplyKeyboardMarkup(
            [['Выбрать другой сезон', 'Поигровая статистика'],
            ['В начало']],
            resize_keyboard=True
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


def flipp_pages(update, context):
    chat = update.effective_chat
    text = (update['message']['text']).rstrip()
    button = telegram.ReplyKeyboardMarkup(
        [['Предыдущие игры'], ['Следующие игры'],
        ['В начало']],
        resize_keyboard=True
    )
    type_statistics = control_panel.get(chat.id).get('statistic_index')
    final_url = control_panel.get(chat.id).get('endpoint')
    current_page = control_panel[chat.id].get('current_page')
    if text == 'Следующие игры':
        page = current_page - 1
    else:
        page = current_page + 1
    control_panel[chat.id]['current_page'] = page
    params = {'page': page}
    response = requests.get(final_url, params=params)
    response = response.json()
    response_list = response.get('data')
    if response_list:
        pages_count = response.get('meta').get('total_pages')
        if page == pages_count:
            button = telegram.ReplyKeyboardMarkup(
                [['Следующие игры'],
                ['В начало']],
                resize_keyboard=True
            )
        if page == 1:
            button = telegram.ReplyKeyboardMarkup(
                [['Предыдущие игры'],
                ['В начало']],
                resize_keyboard=True
            )
        if type_statistics in (STATX_GAME):
            games_count = response.get('meta').get('total_count')
            result = [statistics_per_game(i) for i in response_list]
            response = response_list[0]
            f_n = response.get('player').get('first_name')
            l_n = response.get('player').get('last_name')
            text = ('Статистика игрока *{} {}* по играм:\n\n'
                    'Количество игр в выборке: *{}*\n\n{}').format(
                f_n, l_n, games_count, '\n'.join(reversed(result))
            )
        return context.bot.send_message(
            chat_id=chat.id,
            text=text,
            reply_markup=button,
            parse_mode='Markdown'
        )    
    return context.bot.send_message(
        chat_id=chat.id,
        text='Что то не так',
        reply_markup=button,
        parse_mode='Markdown'
    )  


updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler
updater.dispatcher.add_handler(MessageHandler(Filters.text, answer_hub)) # Filters - обработчики типов сообщений
updater.start_polling(poll_interval=10.0)
updater.idle()
