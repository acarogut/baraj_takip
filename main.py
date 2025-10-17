import time
from bs4 import BeautifulSoup
from selenium import webdriver

driverIst = webdriver.Chrome()
driverIst.get("https://iski.istanbul/baraj-doluluk/")

driverBursa = webdriver.Chrome()
driverBursa.get("https://www.buski.gov.tr/baraj-detay")

driverAnkara = webdriver.Chrome()
driverAnkara.get("https://www.aski.gov.tr/tr/baraj.aspx")

driverIzmir = webdriver.Chrome()
driverIzmir.get("https://www.izsu.gov.tr/tr/BarajlarinSuDurumu/1")

time.sleep(5)

# İstanbul 
soup1 = BeautifulSoup(driverIst.page_source, "html.parser")
ratio1 = soup1.find("div", class_="text-4xl font-bold absolute").get_text(strip=True)
ratio1_num = float(ratio1.replace('%', '').replace(',', '.'))

# Bursa
soup2 = BeautifulSoup(driverBursa.page_source, "html.parser")
ratio2 = soup2.find("span", {"id": "baraj-doluluk-1-info"}).get_text(strip=True)
ratio2_num = float(ratio2.replace('%', '').replace(',', '.'))

# İzmir 
soup3 = BeautifulSoup(driverIzmir.page_source, "html.parser")

toplam_row = soup3.find("span", string=lambda x: x and "Kullanılabilir göl su hacmi" in x).find_parent("tr")
toplam_values = [
    float(td.get_text(strip=True).replace('.', '').replace(',', '.'))
    for td in toplam_row.find_all("td", class_="damtotaltd") if td.get_text(strip=True)
]
toplam_sum = sum(toplam_values)

kullanilabilir_row = soup3.find("span", string=lambda x: x and "Kullanılabilir su hacmi" in x).find_parent("tr")
kullanilabilir_values = [
    float(td.get_text(strip=True).replace('.', '').replace(',', '.'))
    for td in kullanilabilir_row.find_all("td", class_="damtotaltd") if td.get_text(strip=True)
]
kullanilabilir_sum = sum(kullanilabilir_values)

ratio3 = round( kullanilabilir_sum / toplam_sum * 100,2)
ratio3_num = ratio3

#Ankara
soup4 = BeautifulSoup(driverAnkara.page_source, "html.parser")
ratio4 = soup4.find("label", {"id": "LabelBarajOrani"}).get_text(strip=True)
ratio4_num = float(ratio4.replace('%', '').replace(',', '.'))

print("İstanbul Baraj Doluluk Oranı: %", ratio1_num)
print("Bursa Baraj Doluluk Oranı: %", ratio2_num)
print("İzmir Baraj Doluluk Oranı: %", ratio3_num)
print("Ankara Baraj Doluluk Oranı: %", ratio4_num)


driverIst.quit()
driverBursa.quit()
driverAnkara.quit()
driverIzmir.quit()