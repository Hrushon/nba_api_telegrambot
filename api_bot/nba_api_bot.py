"""Телеграм-бот для просмотра статистики NBA."""
import logging
import os
import sys
import re

import requests
import telegram # класс Bot() отправляет сообщения, а класс Updater() получает и обрабатывает сообщения извне

from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from models import game_view, player, team_min, statistics, statistics_per_game
from validator import validator


load_dotenv()

ENDPOINT = 'https://www.balldontlie.io/api/v1/'
ENDPOINT_PHOTO_SEARCH = 'https://imsea.herokuapp.com/api/1?q=nba_'

ADMIN_ID = os.getenv('ADMIN_ID') # Айди аккаунта в телеграм
BOT_TOKEN = os.getenv('BOT_TOKEN') # Токен бота в телеграм

VIEW_GAMES = {
    0: {
        'answer': ['Только плей-офф', 'Все игры'],
        'button' : [['Определенная команда'], ['Все команды'], ['Назад']],
        'text': 'Вам интересны игры всех команд или какой-то конкретной?'
    },
    1: {
        'answer': ['Определенная команда', 'Все команды'],
        'button' : [['Сезон'], ['Временной период'], ['Назад']],
        'text': 'За какой период Вам нужна информация?',
        'additional': 'Ведите ID команды'
    },
    2: {
        'answer': ['Сезон', 'Временной период'],
        'button' : [['Начальная + конечная дата'], ['Конкретный день'], ['Назад']],
        'text': 'За какой период Вам нужна информация?',
        'additional': 'Введите сезон, в пределах которого '
                      'Вас интересует статистика игрока.\n'
                      'К примеру, если требуется статистика игрока за сезон 2016-2017 '
                      'ввести нужно - "*2016*".\n'
                      'Запрос должен содержать только четыре цифры.'
    },
    3: {
        'answer': ['Конкретный день', 'Начальная + конечная дата'],
        'button' : [['В начало'], ['Назад']],
        'text': 'Ограничьте период в следующем формате:\n'
                'Для конкретного дня формат такой: _дд-мм-гггг_\n'
                'Для периода с начальной и конечной датой:\n'
                '_дд-мм-гггг дд-мм-гггг_\n'
                'К примеру, если Вас интересует период с 1 января 2019 года '
                'по 1 марта 2019 года необходимо ввести следующее:\n'
                '*01-01-2019 01-03-2019*\n'
                'А если интересен матч за 1 июля 2021 года, то введите '
                '*01-07-2021*\n'
                'Будьте внимательны при вводе дат.'
    },
    4: {
        'answer': ['', ''],
        'button' : [['В начало'], ['Назад']]
    }
}

VIEW_STATIX = {
    0: {
        'answer': ['Да', 'Нет'],
        'button' : [['Только плей-офф'], ['Все игры'],
                    ['В начало'], ['Назад']],
        'text': 'Все игры или только игры плей-офф?',
        'additional': 'Ведите ID игры\n'
                      '_ID можно узнать в разделе игры_'
    },
    1: {
        'answer': ['Только плей-офф', 'Все игры'],
        'button' : [['Сезон'], ['Временной период'], ['В начало'], ['Назад']],
        'text': 'Все игры или только игры плей-офф?'
    },
    2: {
        'answer': ['Сезон', 'Временной период'],
        'button' : [['Начальная + конечная дата'], ['Конкретный день'],
                    ['В начало'], ['Назад']],
        'text': 'За какой период Вам нужна информация?',
        'additional': 'Введите сезон, в пределах которого '
                      'Вас интересует статистика игрока.\n'
                      'К примеру, если требуется статистика игрока '
                      'за сезон 2016-2017 ввести нужно - "*2016*".\n'
                      'Запрос должен содержать только четыре цифры.'
    },
    3: {
        'answer': ['Конкретный день', 'Начальная + конечная дата'],
        'button' : [['В начало'], ['Назад']],
        'text': 'Ограничьте период в следующем формате:\n'
                'Для конкретного дня формат такой: _дд-мм-гггг_\n'
                'Для периода с начальной и конечной датой:\n'
                '_дд-мм-гггг дд-мм-гггг_\n'
                'К примеру, если Вас интересует период с 1 января 2019 года '
                'по 1 марта 2019 года необходимо ввести следующее:\n'
                '*01-01-2019 01-03-2019*\n'
                'А если интересен матч за 1 июля 2021 года, то введите '
                '*01-07-2021*\n'
                'Будьте внимательны при вводе дат.'
    },
    4: {
        'answer': ['', ''],
        'button' : [['В начало'], ['Назад']]
    }
}

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
        context.user_data.clear()
        return head_page(update, context, False)
    if control_action:
        if text == 'Следующие игры' or text == 'Предыдущие игры':
            return flipp_pages(update, context)
        if control_action.get('games'):
            if control_action.get('games')[-1] == 'preview':
                if text == 'Все игры':
                    control_panel[chat.id]['games'] = 'all_games'
                    return preview_games(update, context)
                if text == 'Игры плей-офф':
                    control_panel[chat.id]['games'] = 'playoff_games'
                    return preview_games(update, context)
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
            if text == 'Статистика по играм':
                control_panel[chat.id]['statistics'] = 'game'
                return preview_statistics(update, context, season=False)
            if text == 'Статистика сезона':
                control_panel[chat.id]['statistics'] = 'season'
                return preview_statistics(update, context)
    if text == 'Игроки и статистика':
        return pre_search_player(update, context)
    if text == 'Команды':
        return view_teams(update, context)
    if text == 'Игры' or context.user_data.get('games') is not None:
        return preview_games(update, context)
    return head_page(update, context)


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


def pre_search_player(update, context):
    chat = update.effective_chat
    flag = {'search_player': 'search_player'}
    control_panel[chat.id] = flag
    button = telegram.ReplyKeyboardMarkup(
        [['Назад'], ['В начало']],
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
            text='Убедитесь что Вы ввели верный запрос на латинице',
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
            str(i['first_name']) + ' ' + str(i['last_name'])
            for i in response_list
        ]
        return context.bot.send_message(
            chat_id=chat.id,
            text=(
                'Уточните поиск - введите имя '
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
            [['Статистика сезона', 'Статистика по играм'],
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


def preview_statistics(update, context):
    chat = update.effective_chat
    answer = (update['message']['text']).rstrip()
    flag_dict = context.user_data.get('statistics')
    button = [['Назад'], ['В начало']]
    text = ''

    if flag_dict is not None:
        count = len(flag_dict)
        print(count)
        print(context.user_data)

        if answer == VIEW_STATIX.get(count).get('answer')[0]:
            text = VIEW_STATIX.get(count).get('additional')
            if text is None:
                context.user_data.get('statistics').append(True)

        elif answer == VIEW_STATIX.get(count).get('answer')[1]:
            context.user_data.get('statistics').append(False)

        elif validator(update, context):
            context.user_data.get('statistics').append(answer)
            if len(context.user_data.get('statistics')) in (1, 3, 5):
                return view_games(update, context) ###################################################################

        else:
            text = 'Попробуйте уточнить запрос. По Вашему запросу ничего не найдено.'

        if not text:
            text = VIEW_STATIX.get(count).get('text')
            button = VIEW_STATIX.get(count).get('button')


    else:
        button = [['Да', 'Нет'], ['Назад'], ['В начало']]
        text = (
            'Вы знаете ID игры и хотите посмотреть детали ее статистики?\n'
            '_ID можно узнать в разделе игры_'
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
            ['Все игры за определенный период'],
            ['Игры плей-офф за определенный период'],
            ['Все игры сезона'],
            ['Игры плей-офф сезона'],
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
        '{}season_averages?season={}&player_ids[]={}'.format(
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


def preview_games(update, context):
    chat = update.effective_chat
    answer = (update['message']['text']).rstrip()
    flag_dict = context.user_data.get('games')
    button = [['Назад']]
    text = ''

    if flag_dict is not None:
        count = len(flag_dict)
        print(count)
        print(context.user_data)

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
            text = 'Попробуйте уточнить запрос. По Вашему запросу ничего не найдено.'

        if not text:
            text = VIEW_GAMES.get(count).get('text')
            button = VIEW_GAMES.get(count).get('button')


    else:
        button = [['Только плей-офф'], ['Все игры'], ['Назад']]
        text = 'Выберите тип игры'
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
            final_url += f'&start_date={start_date}&end_date={end_date}'
        else:
            date = user_data[4]
            final_url += f'&dates[]={date}'


    response = requests.get(final_url)
    final_url = response.url
    print(final_url)
    response = response.json()
    response_list = response.get('data')
    games_count = response.get('meta').get('total_count')
    if games_count and response_list:
        list_games = [game_view(i) for i in response_list]

    return context.bot.send_message(
        chat_id=chat.id,
        text=(
            'Список игр:\nВсего игр: {}\n{}'.format(
                games_count, ('\n'.join(list_games))
            )
        ),
        reply_markup=button,
        parse_mode='Markdown'
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


updater.dispatcher.add_handler(CommandHandler('start', head_page))
updater.dispatcher.add_handler
updater.dispatcher.add_handler(MessageHandler(Filters.text, answer_hub)) # Filters - обработчики типов сообщений
updater.start_polling(poll_interval=10.0)
updater.idle()
