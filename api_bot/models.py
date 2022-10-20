"""Модели для человекочитаемого вывода информации в ответ на запрос."""

FOOT_COEFF = 30.48
INCH_COEFF = 2.54
POUND_COEFF = 0.45

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
    # id = response.get('id')
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
    player_str = '{} {}.\nИграет (или играл перед окончанием карьеры) в {} конференции НБА за команду {} (г. {}) на позиции {}.\n{}\n{}'.format(
        first_name, last_name, CONFERENCE_KIND[conference], team, CITIES_DICT[city], PLAYERS_ROLES[position], height, weight
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
    team_str = '{} или просто {}.\nКоманда из города {} участвует в играх {} конференции НБА.\nАббревиатура команды - {}.\nID - {}.'.format(
        full_name, name, CITIES_DICT[city], CONFERENCE_KIND[conference], abbreviation, id
    )
    return team_str
