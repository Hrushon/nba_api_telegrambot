import requests

ENDPOINT = 'https://www.balldontlie.io/api/v1/'

url = f'{ENDPOINT}/teams'

response = requests.get(url)
