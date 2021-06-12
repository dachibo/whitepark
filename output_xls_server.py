from datetime import datetime
import os
import requests
from config import ip

data = str(datetime.now().date())
if os.path.exists("/var/www/u1250062/data/%s.xls" % data):
    with open("/var/www/u1250062/data/%s.xls" % data, 'rb') as file_bytes:
        headers = {
            'Content-Type': 'text/plain',
        }
        res = requests.post('http://%s/file_output' % ip, headers=headers, data=file_bytes.read())
    print(res)

