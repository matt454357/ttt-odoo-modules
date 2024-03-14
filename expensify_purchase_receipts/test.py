from pprint import pprint
import expensify_test as exp_test
import gzip
from urllib.parse import quote_plus, unquote, unquote_plus
import requests
import json


exp = exp_test.Expensify('aa_matt454357_gmail_com', '0217019ff522301572f050054b91c5e711a4d8dc', '')
msg = exp.get_base_message()
# pprint(msg)
file_name = exp.create_report(msg)
# print(file_name)
res = exp.get_file(file_name)
# pprint(res.text)

data = json.loads(res.text)
pprint(data)
