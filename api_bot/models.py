"""Модели для человекочитаемого вывода информации в ответ на запрос."""
import requests
from datetime import datetime as DT
import pytz



FOOT_COEFF = 30.48
INCH_COEFF = 2.54
PERC_COEFF = 100
POUND_COEFF = 0.45

PLAYERS_ROLES = {
    'G': 'защитник',
    'F': 'форвард',
    'C': 'центровой'
}

CONFERENCE_KIND = {
    'West': 'Западной',
    'East': 'Восточной'
}

CITIES_DICT = {
    'Los Angeles': 'Лос-Анджелес',
    'New York': 'Нью-Йорк',
    'Atlanta': 'Атланта',
    'Boston': 'Бостон',
    'Brooklyn': 'Нью-Йорк',
    'Charlotte': 'Шарлотт',
    'Chicago': 'Чикаго',
    'Cleveland': 'Кливленд',
    'Dallas': 'Даллас',
    'Denver': 'Денвер',
    'Detroit': 'Детройт',
    'Golden State': 'Сан-Франциско',
    'Houston': 'Хьюстон',
    'Indiana': 'Индианаполис',
    'LA': 'Лос-Анджелес',
    'Memphis': 'Мемфис',
    'Miami': 'Майами',
    'Milwaukee': 'Милуоки',
    'Minnesota': 'Миннеаполис',
    'New Orleans': ' Новый Орлеан',
    'Oklahoma City': 'Оклахома-Сити',
    'Orlando': 'Орландо',
    'Philadelphia': 'Филадельфия',
    'Phoenix': 'Финикс',
    'Portland': 'Портленд',
    'Sacramento': 'Сакраменто',
    'San Antonio': 'Сан-Антонио',
    'Toronto': 'Торонто',
    'Utah': 'Юта',
    'Washington': 'Вашингтон',
}

DIVISION_DICT = {
    'Atlantic': 'Атлантический',
    'Northwest': 'Северо-Западный',
    'Pacific': 'Тихоокеанский',
    'Central': 'Центральный',
    'Southwest': 'Юго-Западный',
    'Southeast': 'Юго-Восточный'
}

TZ1 = pytz.timezone('US/Eastern')
TZ2 = pytz.timezone('Europe/Moscow')

response = requests.get('https://www.balldontlie.io/api/v1/teams')
teams_list = response.json().get('data')


def player(response):
    """Модель для профиля игрока."""
    id = response.get('id')
    first_name = response.get('first_name')
    last_name = response.get('last_name')
    position = response.get('position')
    height = weight = ''
    if response.get('height_feet'):
        feet = response.get('height_feet')
        inches = response.get('height_inches')
        height_str = int(feet * FOOT_COEFF + inches * INCH_COEFF)
        height = 'Рост: {} см.'.format(height_str)
    if response.get('weight_pounds'):
        pounds = response.get('weight_pounds')
        weight_str = int(pounds * POUND_COEFF)
        weight = 'Вес: {} кг.'.format(weight_str)
    team = team_max(response.get('team'))
    player_str = (
        '*{} {}*.\n\n'
        '_ID игрока - {}_.\n'
        'Амплуа: {}.\n'
        '{}\n{}\n'
        'Выступает (или выступал перед окончанием карьеры) за команду:\n'
        '{}'
    ).format(
        first_name,
        last_name,
        id,
        PLAYERS_ROLES.get(position, position or '(нет данных)'),
        height,
        weight,
        team
    )
    return player_str


def team_max(response):
    """Модель для профиля команды."""
    id = response.get('id')
    abbreviation = response.get('abbreviation')
    city = response.get('city')
    conference = response.get('conference')
    division = response.get('division')
    full_name = response.get('full_name')
    name = response.get('name')
    team_str = (
        '*{}* или просто *{}* из города {}.\n'
        '_ID команды - {}_.\n'
        'Аббревиатура команды - {}.\n'
        '{} дивизион {} конференции NBA.\n'
    ).format(
        full_name,
        name,
        CITIES_DICT.get(city, city),
        id,
        abbreviation,
        DIVISION_DICT.get(division),
        CONFERENCE_KIND.get(conference, conference)
    )
    return team_str


def team_min(response):
    """Модель для профиля команды в мини-варианте."""
    id = response.get('id')
    abbreviation = response.get('abbreviation')
    city = response.get('city')
    conference = response.get('conference')
    division = response.get('division')
    full_name = response.get('full_name')
    team_str = (
        '_ID - {}_.\n'
        '*{}* ({}).\n'
        'Город {}.\n'
        '{} дивизион {} конференции.\n'
        '------------------------------'
    ).format(
        id,
        full_name,
        abbreviation,
        CITIES_DICT.get(city, city),
        DIVISION_DICT.get(division),
        CONFERENCE_KIND.get(conference, conference)
    )
    return team_str


def statistics(response):
    """Модель для сезонной статистики игрока."""
    games_played = response.get('games_played')
    player_id = response.get('player_id')
    season = response.get('season')
    ast = response.get('ast')
    blk = response.get('blk')
    dreb = response.get('dreb')
    fg3_pct = (response.get('fg3_pct'))
    if 1 > fg3_pct < 0:
        fg3_pct = (response.get('fg3_pct')) * PERC_COEFF
    fg3a = response.get('fg3a')
    fg3m = response.get('fg3m')
    fg_pct = (response.get('fg_pct'))
    if 1 > fg_pct < 0:
        fg_pct = (response.get('fg_pct')) * PERC_COEFF
    fga = response.get('fga')
    fgm = response.get('fgm')
    ft_pct = (response.get('ft_pct'))
    if 1 > ft_pct < 0:
        ft_pct = (response.get('ft_pct')) * PERC_COEFF
    fta = response.get('fta')
    ftm = response.get('ftm')
    min = response.get('min')
    oreb = response.get('oreb')
    pf = response.get('pf')
    pts = response.get('pts')
    reb = response.get('reb')
    stl = response.get('stl')
    turnover = response.get('turnover')
    if season is not None:
        season = '{}-{}'.format(season, season + 1)
    statistics_str = (
        'Сезон: *{}*.\n'
        'Сыгранных игр в сезоне: *{}*.\n'
        'Средние данные за сезон по показателям:\n'
        '+ сыгранные минуты: *{}*\n'
        '+ набранные очки: *{}*\n'
        '+ броски с игры: *{}* из них результативных: *{}*\n'
        '++ точность бросков с игры: *{:.1f}* %\n'
        '+ 3-очковые броски: *{}* из них результативных: *{}*\n'
        '++ точность 3-очковых бросков: *{:.1f}* %\n'
        '+ штрафные броски: *{}* из них результативных: *{}*\n'
        '++ точность штрафных бросков: *{:.1f}* %\n'
        '+ подборы: *{}*, из них в нападении - *{}* и в защите - *{}*\n'
        '+ результативные передачи: *{}*\n'
        '+ перехваты: *{}*\n'
        '+ блоки: *{}*\n'
        '- потери мяча: *{}*\n'
        '- персональные замечания: *{}*\n'
    ).format(
        season, games_played, min, pts, fga, fgm, fg_pct, fg3a,
        fg3m, fg3_pct, fta, ftm, ft_pct, reb, oreb, dreb, ast,
        stl, blk, turnover, pf
    )
    return statistics_str


def statistics_per_game(response):
    """Модель для сезонной статистики по играм."""
    id = response.get('id')
    ast = response.get('ast')
    blk = response.get('blk')
    dreb = response.get('dreb')
    fg3_pct = (response.get('fg3_pct'))
    if 1 > fg3_pct < 0:
        fg3_pct = (response.get('fg3_pct')) * PERC_COEFF
    fg3a = response.get('fg3a')
    fg3m = response.get('fg3m')
    fg_pct = (response.get('fg_pct'))
    if 1 > fg_pct < 0:
        fg_pct = (response.get('fg_pct')) * PERC_COEFF
    fga = response.get('fga')
    fgm = response.get('fgm')
    ft_pct = (response.get('ft_pct'))
    if 1 > ft_pct < 0:
        ft_pct = (response.get('ft_pct')) * PERC_COEFF
    fta = response.get('fta')
    ftm = response.get('ftm')
    game = response.get('game')
    game_id = game.get('id')
    game_date = game.get('date').split('T')[0]
    game_date = game_date.split('-')
    game_date = '-'.join([game_date[2], game_date[1], game_date[0]])
    game_home_team_id = game.get('home_team_id')
    game_home_team_score = game.get('home_team_score')
    game_season = game.get('season')
    game_visitor_team_id = game.get('visitor_team_id')
    game_visitor_team_score = game.get('visitor_team_score')
    min = response.get('min')
    oreb = response.get('oreb')
    pf = response.get('pf')
    player = response.get('player')
    player_id = player.get('id')
    player_first_name = player.get('first_name')
    player_last_name = player.get('last_name')
    player_position = player.get('position')
    player_team_id = player.get('team_id')
    pts = response.get('pts')
    reb = response.get('reb')
    stl = response.get('stl')
    team = response.get('team')
    team_id = team.get('id')
    team_abbreviation = team.get('abbreviation')
    team_city = team.get('city')
    team_conference = team.get('conference')
    team_division = team.get('division')
    team_full_name = team.get('full_name')
    team_name = team.get('name')
    turnover = response.get('turnover')
    if game_season is not None:
        game_season = '{}-{}'.format(game_season, game_season + 1)
    game_home_team_name = teams_list[
        game_home_team_id - 1
    ].get('full_name')
    game_visitor_team_name = teams_list[
        game_visitor_team_id - 1
    ].get('full_name')
    statistics_game_str = (
        'Сезон: {}\n'
        '{}\n'
        '{} против {}\n'
        'Счёт: {}:{}\n'
        'Средняя статистика за игру по показателям:\n'
        '+ сыгранные минуты: *{}*\n'
        '+ набранные очки: *{}*\n'
        '+ броски с игры: *{}* из них результативных: *{}*\n'
        '++ точность бросков с игры: *{:.1f}* %\n'
        '+ 3-очковые броски: *{}* из них результативных: *{}*\n'
        '++ точность 3-очковых бросков: *{:.1f}* %\n'
        '+ штрафные броски: *{}* из них результативных: *{}*\n'
        '++ точность штрафных бросков: *{:.1f}* %\n'
        '+ подборы: *{}*, из них в нападении - *{}* и в защите - *{}*\n'
        '+ результативные передачи: *{}*\n'
        '+ перехваты: *{}*\n'
        '+ блоки: *{}*\n'
        '- потери мяча: *{}*\n'
        '- персональные замечания: *{}*\n'
    ).format(
        game_season, game_date,
        game_home_team_name, game_visitor_team_name, 
        game_home_team_score, game_visitor_team_score,
        min, pts, fga, fgm, fg_pct, fg3a,
        fg3m, fg3_pct, fta, ftm, ft_pct,
        reb, oreb, dreb, ast,
        stl, blk, turnover, pf
    )
    return statistics_game_str


def game_view(response):
    """Модель для представления отдельной игры."""
    id = response.get('id')
    date = response.get('date').split('T')[0]
    date = date.split('-')
    date = '-'.join([date[2], date[1], date[0]])
    home_team_score = response.get('home_team_score')
    visitor_team_score = response.get('visitor_team_score')
    season = int(response.get('season'))
    season = str(season) + '-' + str(season + 1)
    period = response.get('period')
    status = response.get('status')
    time = response.get('time')
    date_time = date + ' ' + status
    postseason = response.get('postseason')
    game_type = 'Регулярный чемпионат'
    if postseason:
        game_type = 'Игры плей-офф'
    home_team = response.get('home_team').get('full_name')
    visitor_team =  response.get('visitor_team').get('full_name')
    if period == 0:
        time = TZ1.localize(
            DT.strptime(date_time, "%d-%m-%Y %I:%M %p")
        ).astimezone(TZ2).strftime("%d-%m-%Y %H:%M")
        time = time.split()
        status_view = (
            'Начало игры {} в {} мск времени.\n'.format(time[0], time[1])
        )
    elif status == 'Final':
        status_view = (
            'Дата {}.\nИгра окончена.\n'.format(date)
        )
    elif status == 'Halftime':
        status_view = (
            'Большой перерыв.\n'
        )
    else:
        status_view = (
            'Идёт {}-ый период.\nВремя игры в периоде {}.\n'.format(status[:1], time)
        )

    game = (
        'Сезон: {}\n'
        '{} против {}\n'
        '{}\n'
        '{}\n'
        'Счёт: {}:{}\n'
    ).format(
        season,
        home_team, visitor_team, game_type,
        status_view,
        home_team_score, visitor_team_score,
    )
    return game
