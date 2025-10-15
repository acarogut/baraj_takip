import csv
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from selenium import webdriver

driver = webdriver.Chrome()  # ChromeDriver PATH’in ayarlı olmalı
driver.get("https://iski.istanbul/baraj-doluluk/")

time.sleep(5)  # JS yüklenmesi için bekle
html = driver.page_source

soup = BeautifulSoup(html, "html.parser")
ratio = soup.find("div", class_="text-4xl font-bold absolute").get_text(strip=True)
print("Baraj Doluluk Oranı:", ratio)

driver.quit()