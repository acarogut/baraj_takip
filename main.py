import time
from datetime import datetime, timedelta
import os
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None
    print("\033[93mMatplotlib bulunamadı; grafik oluşturulamayacak.\033[0m")

try:
    import tweepy  # type: ignore
except Exception:
    tweepy = None

try:
    from dotenv import load_dotenv  # type: ignore
    loaded = load_dotenv()
    if not loaded:
        print("\033[93m.env bulunamadı veya yüklenemedi; ortam değişkenleri eksik olabilir.\033[0m")
except Exception:
    print("\033[93mpython-dotenv yüklü değil; .env okunamadı. X paylaşımı devre dışı kalabilir.\033[0m")

try:
    import requests  # type: ignore
except Exception:
    requests = None


options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driverIst = webdriver.Chrome(options=options)
driverBursa = webdriver.Chrome(options=options)
driverAnkara = webdriver.Chrome(options=options)
driverIzmir = webdriver.Chrome(options=options)


driverIst.get("https://iski.istanbul/baraj-doluluk/")
driverBursa.get("https://www.buski.gov.tr/baraj-detay")
driverAnkara.get("https://www.aski.gov.tr/tr/baraj.aspx")
driverIzmir.get("https://www.izsu.gov.tr/tr/BarajlarinSuDurumu/1")



time.sleep(2)

ratio1_num = 0
ratio2_num = 0
ratio3_num = 0
ratio4_num = 0

try: 
    soup1 = BeautifulSoup(driverIst.page_source, "html.parser")
    ratio1 = soup1.find("div", class_="text-4xl font-bold absolute").get_text(strip=True)
    ratio1_num = float(ratio1.replace('%', '').replace(',', '.'))
except Exception as e:
    pass
print("İstanbul Baraj Doluluk Oranı: %", ratio1_num)

try:
    soup2 = BeautifulSoup(driverBursa.page_source, "html.parser")
    ratio2 = soup2.find("span", {"id": "baraj-doluluk-1-info"}).get_text(strip=True)
    ratio2_num = float(ratio2.replace('%', '').replace(',', '.'))
except Exception as e:
    pass
print("Bursa Baraj Doluluk Oranı: %", ratio2_num)
    

try:
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
except Exception as e:
    pass
print("İzmir Baraj Doluluk Oranı: %", ratio3_num)


try:
    soup4 = BeautifulSoup(driverAnkara.page_source, "html.parser")
    ratio4 = soup4.find("label", {"id": "LabelBarajOrani"}).get_text(strip=True)
    ratio4_num = float(ratio4.replace('%', '').replace(',', '.'))
    print("Ankara Baraj Doluluk Oranı: %", ratio4_num)

except Exception as e:
    print("\033[91mAnkara verisi alınamadı\033[0m")


def create_bar_chart(ist, bursa, izmir, ankara):
    if plt is None:
        return

    data = [("İstanbul", float(ist)), ("Bursa", float(bursa)), ("İzmir", float(izmir)), ("Ankara", float(ankara))]
    data.sort(key=lambda x: x[1], reverse=True)
    cities = [c for c, _ in data]
    values = [v for _, v in data]

    try:
        plt.style.use("seaborn-v0_8")
    except Exception:
        plt.style.use("classic")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    filename = f"baraj_doluluk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    fig, ax = plt.subplots(figsize=(10, 6), dpi=130)
    fig.patch.set_facecolor("#f7f8fa")
    ax.set_facecolor("#fcfdff")
    ax.grid(False)

    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    norm = mcolors.Normalize(vmin=0, vmax=100)
    cmap = cm.get_cmap("RdYlGn")  # 0: kırmızı, 100: yeşil
    colors = [cmap(norm(v)) for v in values]

    bars = ax.bar(cities, values, color=colors, edgecolor="#1b1e23", linewidth=0.6, zorder=3)

    ax.set_ylim(0, 100)
    ax.set_ylabel("Doluluk Oranı (%)", labelpad=8)
    ax.set_title("Baraj Doluluk Oranları", fontsize=16, weight="bold")
    ax.text(0.99, 1.02, f"Güncel: {ts}", ha="right", va="bottom", transform=ax.transAxes, fontsize=9, color="#5a6270")

    ax.text(
        0.5, 0.5, "@baraj_doluluk",
        transform=ax.transAxes,
        fontsize=60,
        color="#2b2b2b",
        alpha=0.06,
        ha="center",
        va="center",
        rotation=30,
        zorder=0,
    )

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.2,
            f"{value:.2f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            weight="bold",
            color="#1b1e23",
        )

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#bfc7d5")
    ax.spines["bottom"].set_color("#bfc7d5")
    ax.tick_params(colors="#3b4150")

    fig.tight_layout(pad=1.5)
    fig.savefig(filename)
    plt.close(fig)
    print(f"Grafik '{filename}' olarak kaydedildi (sıralı ve şık).")
    return filename


def post_image_to_x(image_path, text):
    """X (Twitter) API ile görseli paylaş. .env ile yapılandırılır.

    Gerekli env değişkenleri:
      - X_POST_ENABLED: true/false (varsayılan false)
      - X_TEXT_ONLY: true/false (sadece metin paylaş, varsayılan false)
      - X_API_KEY
      - X_API_SECRET
      - X_ACCESS_TOKEN
      - X_ACCESS_TOKEN_SECRET
    """
    enabled = os.getenv("X_POST_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    text_only = os.getenv("X_TEXT_ONLY", "false").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        print("X paylaşımı devre dışı (X_POST_ENABLED=false).")
        return

    if tweepy is None:
        print("\033[93mTweepy yüklü değil; X paylaşımı atlandı.\033[0m")
        return

    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("\033[93mX API kimlik bilgileri eksik; paylaşım atlandı.\033[0m")
        return

    try:
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api = tweepy.API(auth)

        try:
            me = api.verify_credentials()
            if me:
                print(f"X kimlik doğrulama OK: @{getattr(me, 'screen_name', 'unknown')}")
        except Exception as auth_err:
            print("\033[93mv1.1 kimlik doğrulama başarısız; v2 ile deneme yapılacak.\033[0m")
            print(f"\033[93mDetay: {auth_err}\033[0m")

        text = (text or "").strip()[:270]
        if not text:
            text = "Baraj doluluk oranları"

        if text_only:
            try:
                client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret,
                )
                resp = client.create_tweet(text=text)
                if resp and getattr(resp, 'data', None):
                    print("X metin paylaşımı yapıldı (v2 / 2:tweets).")
                    return
                else:
                    print("\033[93mv2 create_tweet beklenen yanıtı döndürmedi; v1.1 denenecek.\033[0m")
            except Exception as v2_only_err:
                print(f"\033[93mv2 metin paylaşımı başarısız: {v2_only_err}; v1.1 denenecek.\033[0m")

            try:
                api.update_status(status=text)
                print("X metin paylaşımı yapıldı (v1.1).")
            except Exception as v11_only_err:
                print(f"\033[91mX metin paylaşımı başarısız (v1.1): {v11_only_err}\033[0m")
            return

        try:
            media = api.media_upload(image_path)
        except Exception as mu_err:
            print(f"\033[93mMedya yükleme başarısız: {mu_err}; metin-only paylaşım deneniyor.\033[0m")
            try:
                client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret,
                )
                resp = client.create_tweet(text=text)
                if resp and getattr(resp, 'data', None):
                    print("X metin paylaşımı yapıldı (v2 / fallback).")
                else:
                    print("\033[91mMetin paylaşımı fallback yanıtı beklenen formatta değil.\033[0m")
            except Exception as fb_err:
                print(f"\033[91mMetin paylaşımı fallback da başarısız: {fb_err}\033[0m")
            return

        try:
            api.update_status(status=text, media_ids=[media.media_id])
            print("X paylaşımı yapıldı (v1.1).")
        except Exception as post_err:
            msg = str(post_err)
            print(f"\033[93mv1.1 paylaşım başarısız, v2 ile denenecek. Detay: {msg}\033[0m")
            try:
                client = tweepy.Client(
                    consumer_key=api_key,
                    consumer_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_secret,
                )
                resp = client.create_tweet(text=text, media_ids=[media.media_id])
                if resp and getattr(resp, 'data', None):
                    print("X paylaşımı yapıldı (v2 / 2:tweets + media).")
                else:
                    print("\033[91mv2 create_tweet beklenen yanıtı döndürmedi.\033[0m")
            except Exception as v2_err:
                print(f"\033[91mX paylaşımı başarısız (v2): {v2_err}\033[0m")
    except Exception as e:
        print(f"\033[91mX paylaşımı başarısız: {e}\033[0m")


driverIst.quit()
driverBursa.quit()
driverAnkara.quit()
driverIzmir.quit()

png_path = create_bar_chart(ratio1_num, ratio2_num, ratio3_num, ratio4_num)

tweet_text = (
    f"İstanbul %{ratio1_num:.2f} • Bursa %{ratio2_num:.2f} • İzmir %{ratio3_num:.2f} • Ankara %{ratio4_num:.2f}"
)
tmpl = os.getenv("X_TWEET_TEXT")
if tmpl:
    tweet_text = (
        tmpl
        .replace("{{IST}}", f"{ratio1_num:.2f}")
        .replace("{{BURSA}}", f"{ratio2_num:.2f}")
        .replace("{{IZMIR}}", f"{ratio3_num:.2f}")
        .replace("{{ANKARA}}", f"{ratio4_num:.2f}")
    )

# AccuWeather 15 günlük tahminleri çek ve JSON olarak kaydet

def _accu_url_defaults():
    return {
        "Istanbul": os.getenv("ACCU_IST_URL", "https://www.accuweather.com/tr/tr/istanbul/318251/daily-weather-forecast/318251"),
        "Bursa": os.getenv("ACCU_BURSA_URL", "https://www.accuweather.com/tr/tr/bursa/316938/daily-weather-forecast/316938"),
        "İzmir": os.getenv("ACCU_IZMIR_URL", "https://www.accuweather.com/tr/tr/izmir/318316/daily-weather-forecast/318316"),
        "Ankara": os.getenv("ACCU_ANKARA_URL", "https://www.accuweather.com/tr/tr/ankara/316938/daily-weather-forecast/316938"),
    }

def _parse_accu_15day(html):
    bs = BeautifulSoup(html, "html.parser")
    cards = []
    for sel in [
        'a.daily-forecast-card', 'div.daily-forecast-card', 'li.daily-forecast-card',
        '[data-qa="daily-card"]', 'a[data-qa="daily-card"]', 'li[data-qa="daily-card"]',
        'div.forecast-list a', 'li.daily-card', 'div.daily-list a'
    ]:
        cards = bs.select(sel)
        if len(cards) >= 7:
            break
    out = []
    for i, c in enumerate(cards[:15]):
        text = c.get_text(" ", strip=True)
        m_high = re.search(r"(?:(?:High|Maks\.|En Yüksek|Yüksek)\s*:?\s*)?(-?\d{1,2})°", text)
        highs = re.findall(r"(-?\d{1,2})°", text)
        if len(highs) >= 2:
            try:
                h = int(highs[0]); l = int(highs[1])
            except Exception:
                h = int(highs[0]); l = None
        else:
            h = int(m_high.group(1)) if m_high else None
            l = None
        m_prec = re.search(r"(\d{1,2})%", text)
        precip = int(m_prec.group(1)) if m_prec else None
        out.append({"day_index": i+1, "text": text[:200], "high_c": h, "low_c": l, "precip_pct": precip})
    return out

def fetch_accuweather_15day(city, url):
    if requests is None:
        print("requests kütüphanesi yok; AccuWeather alınamadı")
        return []
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"\033[93mAccuWeather {city} için beklenmeyen durum kodu: {resp.status_code}\033[0m")
            return []
        return _parse_accu_15day(resp.text)
    except Exception as e:
        print(f"\033[93mAccuWeather {city} verisi alınamadı: {e}\033[0m")
        return []

def fetch_all_accuweather():
    urls = _accu_url_defaults()
    out = {}
    for city, url in urls.items():
        out[city] = fetch_accuweather_15day(city, url)
    return out

def save_weather_json(weather_by_city, filename=None):
    try:
        if filename is None:
            filename = f"accuweather_15day_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(weather_by_city, f, ensure_ascii=False, indent=2)
        print(f"AccuWeather 15 günlük veriler '{filename}' dosyasına kaydedildi.")
        return filename
    except Exception as e:
        print(f"\033[91mJSON kaydı başarısız: {e}\033[0m")
        return None

def deepseek_summary_week(current_levels, weather_by_city):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or requests is None:
        return None
    payload = {
        "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        "temperature": 0.3,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sen bir baraj su seviyesi tahmin asistanısın. "
                    "Istanbul, Bursa, İzmir, Ankara için mevcut su seviyeleri ve 15 günlük hava durumu (özellikle yağış) göz önünde bulundurarak tam 2 hafta sonraki gün için baraj doluluk tahmininde bulun."
                    "Tahminini yaparken insanların eş zamanlı olarak su kullanacaklarını unutma"
                    "Aralık verme direkt net bir yüzdelik ver."
                    "Cevabını direkt olarak sadece yüzdelik olarak ver, ek açıklama yapma."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "current_levels_pct": current_levels,
                        "weather_15day": weather_by_city,
                        "window_days": 7,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    }
    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload),
            timeout=25,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        msg = data.get("choices", [{}])[0].get("message", {}).get("content")
        if not msg:
            return None
        msg = " ".join(msg.strip().split())
        words = msg.split()
        if len(words) > 50:
            msg = " ".join(words[:50])
        prefix = "Yapay zeka yorumu (tamamen AI tahmini):"
        if not msg.startswith(prefix):
            msg = f"{prefix} {msg}"
        return msg
    except Exception:
        return None

# Fetch weather, build AI summary, then post tweet and save JSON
try:
    weather_by_city = fetch_all_accuweather()
    # Derle mevcut baraj oranları
    current_levels = {
        "İstanbul": round(float(ratio1_num), 2),
        "Bursa": round(float(ratio2_num), 2),
        "İzmir": round(float(ratio3_num), 2),
        "Ankara": round(float(ratio4_num), 2),
    }
    ai_note = deepseek_summary_week(current_levels, weather_by_city)
    if ai_note:
        # Mevcut metne ekle, 270 karakteri aşma
        base = tweet_text
        sep = " — "
        available = 270 - len(base) - len(sep)
        if available > 10:
            tweet_text = base + sep + ai_note[:available]
        else:
            tweet_text = base
    # Artık paylaş
    post_image_to_x(png_path, tweet_text)
    # JSON kaydet
    save_weather_json(weather_by_city)
except Exception as e:
    print(f"\033[93mAccuWeather/DeepSeek işlemi sırasında hata: {e}\033[0m")
