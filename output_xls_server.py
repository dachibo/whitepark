from datetime import datetime
import os
import requests
from config import ip

data = str(datetime.now().date())
name_xls = f'{data}.xls'
if os.path.exists(name_xls):
    with open(f'/var/www/u1250062/data/{name_xls}', 'rb') as file_bytes:
        headers = {
            'Content-Type': 'text/plain',
        }
        res = requests.post(f'http://{ip}/file_xls', headers=headers, data=file_bytes.read())


