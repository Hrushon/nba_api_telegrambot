"""Проверяет правильность вводимых пользователем данных."""
import re


VALID_ETALON = {
    'team_id': [
        '^([1-9]|[12][0-9]|3[0])$'
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



def validator(update, context):
    etalon = VALID_ETALON['team_id'][0]
    text = (update['message']['text']).rstrip()
    return re.match(rf'{etalon}', text)
