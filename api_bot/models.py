"""Модели для человекочитаемого вывода информации в ответ на запрос."""

from lib2to3.pgen2.token import PERCENT


FOOT_COEFF = 30.48
INCH_COEFF = 2.54
POUND_COEFF = 0.45
PERC_COEFF = 100

PLAYERS_ROLES = {
    'G': 'защитника',
    'F': 'форварда',
    'C': 'центрового'
}

CONFERENCE_KIND = {
    'West': 'западной',
    'East': 'восточной'
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


def player(response):
    """Модель для профиля игрока."""
    id = response.get('id')
    first_name = response.get('first_name')
    last_name = response.get('last_name')
    position = response.get('position')
    height = weight = ''
    if response.get('height_feet') is not None:
        feet = response.get('height_feet')
        inches = response.get('height_inches')
        height_str = int(feet * FOOT_COEFF + inches * INCH_COEFF)
        height = 'Рост: {} см.'.format(height_str)
    if response.get('weight_pounds') is not None:
        pounds = response.get('weight_pounds')
        weight_str = int(pounds * POUND_COEFF)
        weight = 'Вес: {} кг.'.format(weight_str)
    team = response.get('team').get('full_name')
    city = response.get('team').get('city')
    conference = response.get('team').get('conference')
    player_str = (
        '{} {}.\n'
        'ID - {}.\n'
        'Выступает (или выступал перед окончанием карьеры) '
        'в {} конференции НБА за команду {} (г. {}) на позиции {}.\n'
        '{}\n{}'
    ).format(
        first_name,
        last_name,
        id,
        CONFERENCE_KIND.get(conference, conference),
        team,
        CITIES_DICT.get(city, city),
        PLAYERS_ROLES.get(position, position),
        height,
        weight
    )
    return player_str


def team(response):
    """Модель для профиля команды."""
    id = response.get('id')
    abbreviation = response.get('abbreviation')
    city = response.get('city')
    conference = response.get('conference')
    division = response.get('division')
    full_name = response.get('full_name')
    name = response.get('name')
    team_str = (
        '{} или просто {}.\n'
        'Команда из города {} участвует в играх {} конференции НБА.\n'
        'Аббревиатура команды - {}.\n'
        'Дивизион - {}.'
        'ID - {}.'
    ).format(
        full_name,
        name,
        CITIES_DICT.get(city, city),
        CONFERENCE_KIND.get(conference, conference),
        abbreviation,
        division,
        id
    )
    return team_str


def statistics(response):
    """Модель для сезонной статистики игрока."""
    games_played = response.get('games_played')
    player_id = response.get('player_id')
    season = response.get('season')
    min = response.get('min')
    fgm = response.get('fgm')
    fga = response.get('fga')
    fg3m = response.get('fg3m')
    fg3a = response.get('fg3a')
    ftm = response.get('ftm')
    fta = response.get('fta')
    oreb = response.get('oreb')
    dreb = response.get('dreb')
    reb = response.get('reb')
    ast = response.get('ast')
    stl = response.get('stl')
    blk = response.get('blk')
    turnover = response.get('turnover')
    pf = response.get('pf')
    pts = response.get('pts')
    fg_pct = (response.get('fg_pct')) * PERC_COEFF
    fg3_pct = (response.get('fg3_pct')) * PERC_COEFF
    ft_pct = (response.get('ft_pct')) * PERC_COEFF
    statistics_str = (
        'Сезон: {}.\n'
        'Сыгранных игр в сезоне: {}.\n'
        'Средние данные за сезон по показателям:\n'
        '+++ набранные очки: {}\n'
        '+++ сыгранные минуты: {}\n'
        '+++ броски с игры: {} из них результативных: {}\n'
        '+++ точность бросков с игры: {:.1f} %\n'
        '+++ 3-очковые броски: {} из них результативных: {}\n'
        '+++ точность 3-очковых бросков: {:.1f} %\n'
        '+++ штрафные броски: {} из них результативных: {}\n'
        '+++ точность штрафных бросков: {:.1f} %\n'
        '+++ подборы: {}, из них в нападении - {} и в защите - {}\n'
        '+++ результативные передачи: {}\n'
        '+++ перехваты: {}\n'
        '+++ блоки: {}\n'
        '+++ потери мяча: {}\n'
        '+++ персональные замечания: {}\n'
    ).format(
        season, games_played, pts, min, fga, fgm, fg_pct, fg3a,
        fg3m, fg3_pct, fta, ftm, ft_pct, reb, oreb, dreb, ast,
        stl, blk, turnover, pf
    )
    return statistics_str

