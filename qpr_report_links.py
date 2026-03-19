import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from tqdm import tqdm

payload = {
    'username': 'admin',
    'pass': 'Admin@1234'
}
cookie = {'PHPSESSID': '55e595625a8b5b1a77e3c2f3387dc2c5779043e9'}

BASE_URL = 'http://wbscps.in/Home_MIS/Home/dashboard/'

# get all links
with requests.Session() as s:
    r = s.post(BASE_URL, cookies=cookie, data=payload)
root = bs(r.text, 'lxml')
nav = root.header
report_tables = []
report_links = []
for url in nav.find_all('a'):
    if "table" in url.get_text('span').strip().lower():
        report_tables.append(url.get_text('span').strip())
        report_links.append(url.get('href'))