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
    }
}


def validator(update, context):
    if context.user_data.get('games'):
        choice_dict = VALID_ETALON['games']
        user_data = context.user_data.get('games')
        idx = len(user_data)
        if idx < 4:
            etalon = choice_dict[idx]
        else:
            etalon = choice_dict[idx]
            if not user_data[3]:
                etalon = choice_dict[idx + 1]

    text = (update['message']['text']).rstrip()
    return re.match(rf'{etalon}', text)
