from datetime import datetime
import os
import requests
from config import ip

data = str(datetime.now().date())
if os.path.exists(f'/var/www/u1250062/data/{data}.xls'):
    with open(f'/var/www/u1250062/data/{data}.xls', 'rb') as file_bytes:
        headers = {
            'Content-Type': 'text/plain',
        }
        res = requests.post(f'http://{ip}/file_xls', headers=headers, data=file_bytes.read())


