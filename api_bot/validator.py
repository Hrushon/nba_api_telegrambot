"""Проверяет правильность вводимых пользователем данных."""
import re

from constants import VALID_ETALONS


def validator(update, context):
    for item in ('games', 'statistics'):
        if context.user_data.get(item) is not None:
            choice_dict = VALID_ETALONS[item]
            user_data = context.user_data.get(item)
            idx = len(user_data)
            etalon = choice_dict.get(idx, '^$')
            if idx > 3:
                if not user_data[3]:
                    etalon = choice_dict[idx + 1]

    for item in ('average', 'player'):
        if context.user_data.get(item) is not None:
            etalon = VALID_ETALONS[item] 

    text = (update['message']['text']).rstrip()
    return re.match(rf'{etalon}', text)
