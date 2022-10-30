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
from exceptions import (
    ApiRequestTrouble,
    ApiStatusTrouble,
    ResponseEmptyFail,
    SendMessageFail
)
from models import (
    game_view, player, team_min,
    statistics_per_season, statistics_per_game
)
from validator import validator


load_dotenv()

ENDPOINT = 'https://www.balldontlie.io/api/v1/'
ENDPOINT_PHOTO_SEARCH = 'https://imsea.herokuapp.com/api/1'

ADMIN_ID = os.getenv('ADMIN_ID') # Айди аккаунта в телеграм
BOT_TOKEN = os.getenv('BOT_TOKEN') # Токен бота в телеграм
TOKENS_NAME = {
    ADMIN_ID: 'ID администратора',
    BOT_TOKEN: 'Токен бота'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


bot = telegram.Bot(token=BOT_TOKEN)
updater = Updater(token=BOT_TOKEN)

cache_dict = {}


def check_tokens():
    """Проверяет наличие токена и ID чата администратора."""
    if all(ADMIN_ID, BOT_TOKEN):
        return True

    for i in (ADMIN_ID, BOT_TOKEN):
        if not i:
            name_token = TOKENS_NAME[i]
            logger.critical(
                'Отсутствует обязательная переменная окружения: '
                '%s. '
                'Программа принудительно остановлена.', name_token
            )
    return False


def check_answer(update, context):
    """
    В зависимости от сообщения пользователя возвращает функцию обработчик.
    Если не выбран ни один обработчик сообщения - возвращает начальное меню.
    """
    text = update.message.text
    if text == 'В начало':
        context.user_data.clear()
        return get_head_page(update, context, False)
    if text == 'Назад':
        return back_to_the_future(update, context)
    if text in ('Следующие игры', 'Предыдущие игры'):
        return flipp_pages(update, context)
    if text == 'Статистика по играм' or context.user_data.get(
        'statistics'
    ) is not None:
        return preview_statistics(update, context)
    if text in (
        'Статистика сезона', 'Выбор другого сезона'
    ) or context.user_data.get('average') is not None:
        return view_season_statistics(update, context)
    if text == 'Игроки и статистика' or context.user_data.get(
        'player'
    ) is not None:
        return search_player(update, context)
    if text == 'Команды':
        return view_teams(update, context)
    if text == 'Игры' or context.user_data.get('games') is not None:
        return preview_games(update, context)
    return get_head_page(update, context, False)


def send_text_message(
    context, chat_id, text, reply_markup, parse_mode='Markdown'
):
    """
    Все текстовые сообщения пользователям в Телеграм отправляются 
    через эту функцию. Перехватывает и логирует возникающие при отправке 
    ошибки.
    """
    logger.info('Начало отправки сообщения ботом.')

    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as error:
        raise SendMessageFail(
            'Сбой при отправке текстового сообщения в Телеграмм. %s', error
        )
    else:
        logger.info('Бот отправил сообщение: %s', text)


def send_photo_message(
    context, chat_id, photo, caption, reply_markup, parse_mode='Markdown'
):
    """
    Все сообщения с фотографиями пользователям в Телеграм отправляются 
    через эту функцию. Перехватывает и логирует возникающие при отправке 
    ошибки.
    """
    logger.info('Начало отправки сообщения ботом.')

    try:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as error:
        raise SendMessageFail(
            'Сбой при отправке сообщения с фото в Телеграмм. %s', error
        )
    else:
        logger.info('Бот отправил сообщение: \n%s\n$s', photo, caption)


def check_api_answer(endpoint, params):
    """
    Посредством этой функции производятся все запросы к внешним сервисам API.
    Функция проверяет HTTP-статус полученного ответа от API-сервиса, а также 
    перехватывает и логирует все ошибки при отправке запросов.
    """
    logger.info('Начало проверки корректности запроса к API.')
    try:
        response = requests.get(endpoint, params=params)
    except Exception as error:
        raise ApiRequestTrouble(
            'Сбой при запросе к эндпоинту %s.'
            'Параметры запроса: %s.'
            'Ошибка: %s', endpoint, params, error
        )
    else:
        if response.status_code != HTTPStatus.OK:
            raise ApiStatusTrouble(
                'Сбой при запросе к эндпоинту %s. '
                'Код ответа API: %s.'
                'Параметры запроса: %s.',
                endpoint, response.status_code, params
            )
        endpoint = response.url
        response = response.json()
        return check_response_content(response, endpoint)


def check_response_content(response, endpoint):
    """
    Функция проверяет структуру ответа API-сервиса на корректность 
    и логирует все ошибки.
    """
    logger.info('Начало проверки корректности структуры ответа API.')
    if not isinstance(response, dict):
        raise TypeError(
            f'Ответ API c эндпоинта: {endpoint} пришел не в виде словаря.'
        )
    for item in ('data', 'meta'):
        if item not in response:
            raise KeyError(
                f'Отсутствует ключ {item} в ответе API c эндпоинта: '
                f'{endpoint}.'
            )
    data = response.get('data')
    if not isinstance(data, list):
        raise TypeError(
            f'Значение data ответа API c эндпоинта: {endpoint} '
            f'пришел не в виде списка.'
        )
    meta = response.get('meta')
    if not isinstance(meta, dict):
        raise TypeError(
            f'Значение data ответа API c эндпоинта: {endpoint} '
            f'пришел не в виде словаря.'
        )
    if not data or meta:
        raise ResponseEmptyFail(
            f'Пришел пустой ответ API c эндпоинта: {endpoint}.'
        )
    return response


def get_head_page(update, context, start=True):
    """
    Функция возвращает главную страницу (начальное меню).
    Немного видоизменяется в зависимости от типа сообщения.
    По умолчанию возвращает ответ на команду /start с текстом приветствия.
    При вызове от MessageHandler получает аргумент start=False.
    """
    chat = update.effective_chat
    name = update.message.chat.first_name
    text = f'Чем я могу Вам помочь, {name}?'
    if start:
        text = f'Спасибо, что включили меня, {name}!'
    send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            [['Игры'], ['Команды'], ['Игроки и статистика']],
            resize_keyboard=True
        )
    )


def back_to_the_future(update, context):
    """
    Функция возврата на один шаг назад в диалоговом меню.
    Вызывается в случае нажатия пользователем кнопки 'Назад'.
    При нахождении пользователя в диалоговом меню 
    'Игры' или 'Игроки и статистика' возвращает пользователя к предыдущему
    этапу выбора ответа.
    В иных случаях вызывает функцию возврата главного меню.
    """
    back_func_choice = {
        'games': preview_games,
        'statistics': preview_statistics
    }

    for item in ('games', 'statistics'):
        flag = context.user_data.get(item)
        if flag is not None:
            count = len(flag)
            if count != 0:
                flag.pop()
            else:
                context.user_data.pop(item)
            return back_func_choice[item](update, context)            

    return get_head_page(update, context)


def search_player(update, context):
    """
    Функция поиска игрока. Выполняет поиск игрока по имени на латинице. 
    При необходимости уточняет запрос. Валидация введенного имени происходит 
    в функции validator(). 
    JSON-ответ обрабатывает с помощью функции player() модуля models. 
    Полученные данные игрока (ID, first_name, last_name) сохраняет в 
    словарь user_data объекта context для возможности использования 
    в других функциях.
    По итогу возвращает пользователю данные игрока с фотографией 
    (но сервис API по поиску фотографий что-то стал отваливаться) или 
    без неё и предлагает ознакомиться со статистикой игрока.
    """
    endpoint = f'{ENDPOINT}players'
    chat = update.effective_chat
    answer = update.message.text
    flag_dict = context.user_data.get('player')
    text = (
        'Введите имя игрока, которого Вы хотите найти. '
        '*Запрос должен быть на латинице*.'
    )
    button = [['В начало']]

    if flag_dict is not None:
        if validator(update, context):
            answer = '_'.join((answer).split(' '))
            params = {'per_page': 25, 'search': answer}
            response = requests.get(endpoint, params=params)
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
                    'из предложенного списка:\n_{}_'.format(
                        '\n'.join(list_name)
                    )
                )
            elif response_list:
                endpoint = ENDPOINT_PHOTO_SEARCH
                response = response_list[0]
                player_id = response.get('id')
                first_name = response.get('first_name')
                last_name = response.get('last_name')
                context.user_data.get('player').extend(
                    (player_id, first_name, last_name)
                )
                text = player(response)
                info_for_photo = f'nba_{first_name}_{last_name}'
                params = {'q': info_for_photo}
                photo = requests.get(endpoint, params=params)
                button = [
                    ['Статистика сезона', 'Статистика по играм'],
                    ['В начало']
                ]
                if photo.status_code == HTTPStatus.OK:
                    photo = photo.json()['results'][0]
                    return send_photo_message(
                        context=context,
                        chat_id=chat.id,
                        photo=photo,
                        caption=text,
                        reply_markup=button
                    )

        else:
            text = ('Введенный запрос не прошел проверку.\n'
                   'Убедитесь что Вы ввели верный запрос на латинице')

    else:
        context.user_data['player'] = []

    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


def view_teams(update, context):
    """
    Функция отображения списка текущих команд НБА.
    В случае отсутствия списка команд в 'кэше' достает список команд из 
    запроса к API. В остальных случаях - достает из 'кэша'.
    Список в 'кэше' обновляется каждый месяц. 
    JSON-ответ обрабатывает с помощью функции team_min() модуля models.
    """
    endpoint = f'{ENDPOINT}teams'
    chat = update.effective_chat
    date = datetime.now()
    flag = f'list_teams_{date.month}_{date.year}'
    if cache_dict.get(flag):
        response = requests.get(endpoint)
        response = response.json()
        response_list = response.get('data')
        teams_count = response.get('meta').get('total_count')
        if teams_count and response_list:
            list_teams = [team_min(i) for i in response_list]
            cache_dict[flag] = list_teams
    list_teams = cache_dict.get(flag)
    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=(
            'Список текущих команд NBA:\n\n{}'.format('\n'.join(list_teams))
        ),
        reply_markup=telegram.ReplyKeyboardMarkup(
            [['В начало']],
            resize_keyboard=True
        )
    )


def preview_statistics(update, context):
    """
    Функция возвращает этапы диалога с пользователем для уточнения параметров 
    выбора статистики игрока.
    По результатам диалога в словаре user_data объекта context создается 
    список параметров с ключом 'statistics', который будет использован 
    функцией view_statistics(). Список вопросов, уточняющих вопросов и 
    наборы кнопок диалогового меню находятся в словаре VIEW_STATIX 
    модуля constants. Ответы пользователя на уточняющие вопросы проходят 
    валидацию в функции validator().
    """
    chat = update.effective_chat
    answer = update.message.text
    flag_dict = context.user_data.get('statistics')
    button = [['Назад'], ['В начало']]

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
            text = 'Попробуйте уточнить запрос. Ответа не найдено.'

        if text is None or answer == 'Назад':
            text = VIEW_STATIX.get(count).get('text')
            button = VIEW_STATIX.get(count).get('button')

    else:
        button = [['Да', 'Нет'], ['В начало']]
        text = (
            'Вы знаете ID игры и хотите посмотреть детали ее статистики?\n\n'
            '_ID игры можно узнать в разделе "Игры"_'
        )
        context.user_data['statistics'] = []

    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


def view_statistics(update, context):
    """
    Функция отображения статистики игрока по играм.
    Получает данные из словаря user_data объекта context об игроке и 
    параметрах выборки. 
    Создает из параметров запрос, обрабатывает ответ и предоставляет его 
    пользователю.
    JSON-ответ обрабатывает с помощью функции statistics_per_game() 
    модуля models.
    В случае большого количества игр предоставляет пользователю 
    возможность листания страниц через функцию flipp_pages(). 
    Для этого сохраняет в словарь user_data объекта context две 
    записи, содержащие эндпоинт и текущую страницу.
    """
    endpoint = f'{ENDPOINT}stats'
    chat = update.effective_chat
    button = [['В начало']]
    text='Статистики за данный период не найдено'
    player = context.user_data.get('player')
    if player:
        player_id, first_name, last_name = player[0], player[1], player[2]
    user_data = context.user_data.get('statistics')
    game_id, playoff, season = user_data[0], user_data[1], user_data[2]
    params ={
        'per_page': 5,
        'player_ids': player_id,
        'postseason': playoff,
        'game_ids': game_id,
        'seasons': season
    }

    if not isinstance(season, str):
        if not user_data[3]:
            user_data = (user_data[4]).split(' ')
            start_date, end_date = *user_data,
            start_date = '-'.join(reversed(start_date.split('-')))
            end_date = '-'.join(reversed(end_date.split('-')))
            pairs = {'start_date': start_date, 'end_date': end_date}
            params.update(pairs)
        else:
            date = user_data[4]
            params.update({'dates': date})

    response = requests.get(endpoint, params=params)
    final_url = response.url
    response = response.json()
    response_list = response.get('data')
    games_count = response.get('meta').get('total_count')
    pages_count = response.get('meta').get('total_pages')
    if response_list and games_count:
        result = [statistics_per_game(i) for i in response_list]
        if pages_count > 1:
            page = pages_count
            button = [['Следующие игры'], ['В начало']]
            context.user_data['current_endpoint'] = final_url
            context.user_data['current_page'] = page
            params.update({'page': page})
            response = requests.get(endpoint, params=params)
            response = response.json()
            response_list = response.get('data')
            result = [statistics_per_game(i) for i in response_list]

        text = ('Статистика игрока *{} {}* по играм:\n\n'
                'Количество игр в выборке: *{}*\n\n{}').format(
            first_name, last_name, games_count, '\n'.join(reversed(result))
        )

    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


def view_season_statistics(update, context):
    """
    Функция возвращает пользователю данные статистики игрока 
    за конкретный сезон. 
    Данные об игроке получает из словаря user_data объекта 
    context. Валидацию ответа пользователя производит с помощью функции 
    validator().
    JSON-ответ обрабатывает с помощью функции statistics_per_season() 
    модуля models.
    """
    endpoint = f'{ENDPOINT}season_averages'
    chat = update.effective_chat
    button = [['В начало']]
    text = (
        'Введите сезон, в пределах которого '
        'Вас интересует статистика игрока.\n'
        'К примеру, если требуется статистика игрока '
        'за сезон 2016-2017 ввести нужно - "*2016*".\n'
        'Запрос должен содержать только четыре цифры.'
    )
    answer = update.message.text
    flag_dict = context.user_data.get('average')
    player = context.user_data.get('player')
    if player:
        player_id, first_name, last_name = player[0], player[1], player[2]

    if flag_dict is not None and answer != 'Выбрать другой сезон':
        if validator(update, context):
            params = {
                'season': answer,
                'player_ids': player_id
            }
            response = requests.get(endpoint, params=params)
            response = response.json()
            response_list = response.get('data')
            if response_list:
                response = response_list[0]
                result = statistics_per_season(response)
                text = (f'Статистика игрока *{first_name} {last_name}*:'
                        f'\n\n{result}')
                button = [
                    ['Выбрать другой сезон', 'Статистика по играм'],
                    ['В начало']
                ]
        else:
            text = ('Убедитесь, что Вы ввели верный запрос')

    else:
        context.user_data['average'] = []

    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


def preview_games(update, context):
    """
    Функция возвращает этапы диалога с пользователем для уточнения параметров 
    выборки отображения игр.
    По результатам диалога в словаре user_data объекта context создается 
    список параметров с ключом 'games', который будет использован функцией 
    view_games(). Список вопросов, уточняющих вопросов и наборы кнопок 
    диалогового меню находятся в словаре VIEW_GAMES модуля constants. 
    Ответы пользователя на уточняющие вопросы проходят валидацию 
    в функции validator().
    """
    chat = update.effective_chat
    answer = update.message.text
    flag_dict = context.user_data.get('games')
    button = [['Назад'], ['В начало']]

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

        if text is None or answer == 'Назад':
            text = VIEW_GAMES.get(count).get('text')
            button = VIEW_GAMES.get(count).get('button')

    else:
        text = 'Какие игры Вас интересуют?'
        button = [['Только плей-офф'], ['Все игры'], ['В начало']]
        context.user_data['games'] = []

    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


def view_games(update, context):
    """
    Функция отображения игр в рамках выборки пользователя.
    Получает данные из user_data объекта context о параметрах выборки. 
    Создает из параметров запрос, обрабатывает ответ и предоставляет его 
    пользователю. 
    JSON-ответ обрабатывает с помощью функции game_view() модуля models.
    В случае большого количества игр предоставляет пользователю 
    возможность 'листания страниц' через функцию flipp_pages(). 
    Для этого сохраняет в словарь user_data объекта context две 
    записи, содержащие эндпоинт и текущую страницу.
    """
    endpoint = f'{ENDPOINT}games'
    chat = update.effective_chat
    button = [['В начало']]
    text='Игр за данный период не найдено'
    user_data = context.user_data.get('games')
    playoff, team_id, season = user_data[0], user_data[1], user_data[2]
    params ={
        'per_page': 5,
        'postseason': playoff,
        'team_ids': team_id,
        'seasons': season
    }

    if not isinstance(season, str):
        if not user_data[3]:
            user_data = (user_data[4]).split(' ')
            start_date, end_date = *user_data,
            start_date = '-'.join(reversed(start_date.split('-')))
            end_date = '-'.join(reversed(end_date.split('-')))
            pairs = {'start_date': start_date, 'end_date': end_date}
            params.update(pairs)
        else:
            date = user_data[4]
            params.update({'dates': date})

    response = requests.get(endpoint, params=params)
    final_url = response.url
    response = response.json()
    response_list = response.get('data')
    games_count = response.get('meta').get('total_count')
    pages_count = response.get('meta').get('total_pages')
    if games_count and response_list:
        result = [game_view(i) for i in response_list]
        if pages_count > 1:
            page = pages_count
            button = [['Следующие игры'], ['В начало']]
            context.user_data['current_endpoint'] = final_url
            context.user_data['current_page'] = page
            params.update({'page': page})
            response = requests.get(endpoint, params=params)
            response = response.json()
            response_list = response.get('data')
            result = [game_view(i) for i in response_list]

        text = ('Количество игр в выборке: *{}*\nСписок игр:\n{}'.format(
                games_count, '\n'.join(reversed(result))
        ))
 
    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


def flipp_pages(update, context):
    """
    Функция позволяет пользователю 'листать страницы' в случае 
    получения большого количества игр по результатам выборки.
    Необходимые параметры: эндпоинт и текущую страницу получает 
    из словаря user_data объекта context. Оттуда же достает 
    сведения о типе отображаемых данных - 'статистика игрока' 
    или 'список игр' - для вызова необходимой функции обработки 
    и представления полученной информации.
    """
    text = 'Что-то не так'
    chat = update.effective_chat
    answer = update.message.text
    button = [['Предыдущие игры'], ['Следующие игры'], ['В начало']]
    endpoint = context.user_data.get('current_endpoint')
    current_page = context.user_data.get('current_page')
    if answer == 'Следующие игры':
        page = current_page - 1
    else:
        page = current_page + 1
    context.user_data['current_page'] = page
    params = {'page': page}
    response = requests.get(endpoint, params=params)
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
 
    return send_text_message(
        context=context,
        chat_id=chat.id,
        text=text,
        reply_markup=telegram.ReplyKeyboardMarkup(
            button,
            resize_keyboard=True
        )
    )


updater.dispatcher.add_handler(CommandHandler('start', get_head_page))
updater.dispatcher.add_handler(MessageHandler(Filters.all, check_answer))
updater.start_polling(poll_interval=5.0)
updater.idle()
