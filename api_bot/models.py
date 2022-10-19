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
    'Atlanta':,
    'Boston':,
    'Brooklyn':,
    'Charlotte':,
    'Chicago':,
    'Cleveland':,
    'Dallas':,
    'Denver':,
    'Detroit':,
    'Golden State':,
    'Houston':,
    'Indiana':,
    'LA': 'Лос-Анджелес',
    'Memphis':,
    'Miami':,
    'Milwaukee':,
    'Minnesota':,
    'New Orleans':,
    'Oklahoma City':,
    'Orlando':,
    'Philadelphia':,
    'Phoenix':,
    'Portland':,
    'Sacramento':,
    'San Antonio':,
    'Toronto':,
    'Utah':,
    'Washington':,
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
    player_str = '{} {}.\nИграет (или играл) в {} конференции за команду {} из города {} на позиции {}.\n{}\n{}'.format(
        first_name, last_name, CONFERENCE_KIND[conference], team, CITIES_DICT[city], PLAYERS_ROLES[position], height, weight
    )
    return player_str
    


