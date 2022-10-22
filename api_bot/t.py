import re


text = '1956'


print(re.match(r'^[\d+]{4}$', text))

if re.match(r'^[\d+]{4}$', text) is None:
    print('None')
else:
    print('Yes')
