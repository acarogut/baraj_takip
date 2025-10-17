import time
from bs4 import BeautifulSoup
from selenium import webdriver

driverIst = webdriver.Chrome()
driverIst.get("https://iski.istanbul/baraj-doluluk/")

driverBursa = webdriver.Chrome()
driverBursa.get("https://www.buski.gov.tr/baraj-detay")

time.sleep(5)

# İstanbul 
soup1 = BeautifulSoup(driverIst.page_source, "html.parser")
ratio1 = soup1.find("div", class_="text-4xl font-bold absolute").get_text(strip=True)

# Bursa
soup2 = BeautifulSoup(driverBursa.page_source, "html.parser")
ratio2 = soup2.find("span", {"id": "baraj-doluluk-1-info"}).get_text(strip=True)

print("İstanbul Baraj Doluluk Oranı:", ratio1)
print("Bursa Baraj Doluluk Oranı:", ratio2)

driverIst.quit()
driverBursa.quit()