"""Проверяет правильность вводимых пользователем данных."""
import re


VALID_ETALON = { 
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


def validator(update, context):
    if context.user_data.get('games') is not None:
        choice_dict = VALID_ETALON['games']
        user_data = context.user_data.get('games')
        idx = len(user_data)
        etalon = choice_dict.get(idx, '^$')
        if idx > 3:
            if not user_data[3]:
                etalon = choice_dict[idx + 1]

    elif context.user_data.get('statistics') is not None:
        choice_dict = VALID_ETALON['statistics']
        user_data = context.user_data.get('statistics')
        idx = len(user_data)
        etalon = choice_dict.get(idx, '^$')
        if idx > 3:
            if not user_data[3]:
                etalon = choice_dict[idx + 1]

    elif context.user_data.get('average') is not None:
        etalon = VALID_ETALON['average']

    elif context.user_data.get('player') is not None:
        etalon = VALID_ETALON['player']  

    text = (update['message']['text']).rstrip()
    return re.match(rf'{etalon}', text)
