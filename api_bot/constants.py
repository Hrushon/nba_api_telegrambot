"""Модуль с константами для работы телеграм-бота NBA."""

CITIES = {
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

CONFERENCE_KIND = {
    'West': 'Западной',
    'East': 'Восточной'
}

DIVISIONS = {
    'Atlantic': 'Атлантический',
    'Northwest': 'Северо-Западный',
    'Pacific': 'Тихоокеанский',
    'Central': 'Центральный',
    'Southwest': 'Юго-Западный',
    'Southeast': 'Юго-Восточный'
}

FOOT_COEFF = 30.48

INCH_COEFF = 2.54

PERC_COEFF = 100

PLAYERS_ROLES = {
    'G': 'защитник',
    'F': 'форвард',
    'C': 'центровой'
}

POUND_COEFF = 0.45

TIME_OUT = 60

VALID_ETALONS = { 
    'games': {
        1: '^([1-9]|[12][0-9]|3[0])$',
        2: '^[\d+]{4}$',
        4: (
            '^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d)$'
        ),
        5: (
            '^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d) '
            '(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d)$'
        )
    },
    'statistics': {
        0: '^[\d]+$',
        2: '^[\d+]{4}$',
        4: (
            '^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d)$'
        ),
        5: (
            '^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d) '
            '(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-((19|20)\d\d)$'
        )
    },
    'player': '^[a-zA-Z ]+$',
    'average': '^[\d+]{4}$'
}

VIEW_GAMES = {
    0: {
        'answer': ['Только плей-офф', 'Все игры'],
        'button' : [['Определенная команда'], ['Все команды'],
                    ['Назад'], ['В начало']],
        'text': 'Вам интересны игры всех команд или какой-то конкретной?'
    },
    1: {
        'answer': ['Определенная команда', 'Все команды'],
        'button' : [['Сезон'], ['Временной период'], ['Назад'], ['В начало']],
        'text': 'За какой период Вам нужна информация?',
        'additional': 'Ведите ID команды'
    },
    2: {
        'answer': ['Сезон', 'Временной период'],
        'button' : [['Начальная + конечная дата'], ['Конкретный день'],
                    ['Назад'], ['В начало']],
        'text': 'Вы хотите указать конкретную дату или временной период?',
        'additional': 'Введите сезон, игры в пределах которого '
                      'Вас интересуют.\n'
                      'К примеру, если требуется статистика игр '
                      'за сезон 2016-2017 '
                      'ввести нужно - "*2016*".\n'
                      'Запрос должен содержать только четыре цифры.'
    },
    3: {
        'answer': ['Конкретный день', 'Начальная + конечная дата'],
        'button' : [['Назад'], ['В начало']],
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
        'button' : [['Назад'], ['В начало']]
    }
}

VIEW_STATIX = {
    0: {
        'answer': ['Да', 'Нет'],
        'button' : [['Только плей-офф'], ['Все игры'],
                    ['Назад'], ['В начало']],
        'text': 'Все игры или только игры плей-офф?',
        'additional': 'Ведите ID игры\n'
                      '_ID можно узнать в разделе игры_'
    },
    1: {
        'answer': ['Только плей-офф', 'Все игры'],
        'button' : [['Сезон'], ['Временной период'], ['Назад'], ['В начало']],
        'text': 'Игры сезона или Вас интересует конкретный временной период?'
    },
    2: {
        'answer': ['Сезон', 'Временной период'],
        'button' : [['Начальная + конечная дата'], ['Конкретный день'],
                    ['Назад'], ['В начало']],
        'text': 'За какой период Вам нужна информация?',
        'additional': 'Введите сезон, в пределах которого '
                      'Вас интересует статистика игрока.\n'
                      'К примеру, если требуется статистика игрока '
                      'за сезон 2016-2017 ввести нужно - "*2016*".\n'
                      'Запрос должен содержать только четыре цифры.'
    },
    3: {
        'answer': ['Конкретный день', 'Начальная + конечная дата'],
        'button' : [['Назад'], ['В начало']],
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
        'button' : [['Назад'], ['В начало']]
    }
}
