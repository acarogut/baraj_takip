import time
from datetime import datetime
import os
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def parse_percentage(text: str, default: float = 0.0) -> float:
    try:
        cleaned = text.replace("%", "").replace(",", ".").strip()
        return float(cleaned)
    except (AttributeError, ValueError):
        return default


def _sum_row(row) -> float:
    if not row:
        return 0.0
    parent = row.find_parent("tr")
    if parent is None:
        return 0.0
    total = 0.0
    for cell in parent.find_all("td", class_="damtotaltd"):
        value = cell.get_text(strip=True)
        if not value:
            continue
        try:
            total += float(value.replace(".", "").replace(",", "."))
        except ValueError:
            continue
    return total


plt = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    log("\033[93mMatplotlib bulunamadı; grafik oluşturulamayacak.\033[0m")

try:
    import tweepy
except ImportError:
    tweepy = None

try:
    from dotenv import load_dotenv
    if not load_dotenv():
        log("\033[93m.env bulunamadı veya yüklenemedi; ortam değişkenleri eksik olabilir.\033[0m")
except ImportError:
    log("\033[93mpython-dotenv yüklü değil; .env okunamadı. X paylaşımı devre dışı kalabilir.\033[0m")

try:
    import requests
except ImportError:
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

soup1 = BeautifulSoup(driverIst.page_source, "html.parser")
ratio1_node = soup1.find("div", class_="text-4xl font-bold absolute")
ratio1_num = parse_percentage(ratio1_node.get_text(strip=True) if ratio1_node else "", 0.0)
log(f"İstanbul Baraj Doluluk Oranı %{ratio1_num:.2f}")

soup2 = BeautifulSoup(driverBursa.page_source, "html.parser")
ratio2_node = soup2.find("span", {"id": "baraj-doluluk-1-info"})
ratio2_num = parse_percentage(ratio2_node.get_text(strip=True) if ratio2_node else "", 0.0)
log(f"Bursa Baraj Doluluk Oranı %{ratio2_num:.2f}")

soup3 = BeautifulSoup(driverIzmir.page_source, "html.parser")
toplam_row = soup3.find("span", string=lambda x: x and "Kullanılabilir göl su hacmi" in x)
kullanilabilir_row = soup3.find("span", string=lambda x: x and "Kullanılabilir su hacmi" in x)

toplam_sum = _sum_row(toplam_row)
kullanilabilir_sum = _sum_row(kullanilabilir_row)
ratio3_num = round(kullanilabilir_sum / toplam_sum * 100, 2) if toplam_sum else 0.0
log(f"İzmir Baraj Doluluk Oranı %{ratio3_num:.2f}")

soup4 = BeautifulSoup(driverAnkara.page_source, "html.parser")
ratio4_node = soup4.find("label", {"id": "LabelBarajOrani"})
ratio4_num = parse_percentage(ratio4_node.get_text(strip=True) if ratio4_node else "", 0.0)
if ratio4_node:
    log(f"Ankara Baraj Doluluk Oranı %{ratio4_num:.2f}")
else:
    log("\033[91mAnkara verisi alınamadı\033[0m")


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
    cmap = plt.colormaps["RdYlGn"]
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
    log(f"Grafik '{filename}' olarak kaydedildi.")
    return filename

def post_image_to_x(image_path, text):
    enabled = os.getenv("X_POST_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
    text_only = os.getenv("X_TEXT_ONLY", "false").lower() in {"1", "true", "yes", "on"}
    if not enabled:
        log("X paylaşımı devre dışı (X_POST_ENABLED=false).")
        return

    if tweepy is None:
        log("\033[93mTweepy yüklü değil; X paylaşımı atlandı.\033[0m")
        return

    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        log("\033[93mX API kimlik bilgileri eksik; paylaşım atlandı.\033[0m")
        return

    try:
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
        api = tweepy.API(auth)
    except Exception as exc:
        log(f"\033[91mX paylaşımı için kimlik doğrulama yapılamadı: {exc}\033[0m")
        return

    client = None
    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
    except Exception:
        client = None

    prepared_text = (text or "").strip()[:270]
    if not prepared_text:
        prepared_text = "Baraj doluluk oranları"

    if text_only:
        if client:
            try:
                resp = client.create_tweet(text=prepared_text)
                if resp and getattr(resp, "data", None):
                    log("X metin paylaşımı yapıldı (v2).")
                    return
            except Exception as exc:
                log(f"\033[93mv2 metin paylaşımı başarısız: {exc}\033[0m")
        try:
            api.update_status(status=prepared_text)
            log("X metin paylaşımı yapıldı (v1.1).")
        except Exception as exc:
            log(f"\033[91mX metin paylaşımı başarısız: {exc}\033[0m")
        return

    try:
        media = api.media_upload(image_path)
    except Exception as exc:
        log(f"\033[93mMedya yükleme başarısız: {exc}\033[0m")
        if client:
            try:
                resp = client.create_tweet(text=prepared_text)
                if resp and getattr(resp, "data", None):
                    log("X metin paylaşımı yapıldı (v2).")
                    return
            except Exception as fallback_err:
                log(f"\033[91mMetin paylaşımı fallback başarısız: {fallback_err}\033[0m")
        return

    try:
        api.update_status(status=prepared_text, media_ids=[media.media_id])
        log("X paylaşımı yapıldı (v1.1).")
    except Exception as exc:
        exc_text = str(exc)
        if "403 Forbidden" not in exc_text or "453" not in exc_text:
            log(f"\033[93mv1.1 paylaşım başarısız: {exc_text}; v2 denenecek.\033[0m")
        if client:
            try:
                resp = client.create_tweet(text=prepared_text, media_ids=[media.media_id])
                if resp and getattr(resp, "data", None):
                    log("X paylaşımı yapıldı (v2).")
                else:
                    log("\033[91mv2 paylaşım beklenen yanıtı döndürmedi.\033[0m")
            except Exception as v2_err:
                log(f"\033[91mX paylaşımı başarısız (v2): {v2_err}\033[0m")


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
            except ValueError:
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
        log("requests kütüphanesi yok; AccuWeather alınamadı")
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
            log(f"\033[93mAccuWeather {city} için beklenmeyen durum kodu: {resp.status_code}\033[0m")
            return []
        return _parse_accu_15day(resp.text)
    except Exception as e:
        log(f"\033[93mAccuWeather {city} verisi alınamadı: {e}\033[0m")
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
        log(f"AccuWeather 15 günlük veriler '{filename}' dosyasına kaydedildi.")
        return filename
    except Exception as e:
        log(f"\033[91mJSON kaydı başarısız: {e}\033[0m")
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
                    "Sen bir baraj su seviyesi tahmin asistanısın."
                    "Istanbul, Bursa, İzmir, Ankara için mevcut su seviyeleri ve 15 günlük hava durumu (özellikle yağış) göz önünde bulundurarak tam 2 hafta sonraki gün için baraj doluluk tahmininde bulun."
                    "Tahminini yaparken insanların eş zamanlı olarak su kullanacaklarını unutma"
                    "Aralık verme direkt net bir yüzdelik ver."
                    "Cevabını Türkçe ver."
                    "Daha inandırıcı olması için açıklama yapabilirsin."
                    "Örnek cevap: Hali hazırda alınan tasarruf önlemleri, İstanbul ilinin günlük su tüketimi, 14 günlük detaylı hava durumu, yağışların bölgeleri ve oranları baz alınarak 12 Kasım 2025 tarihinde İstanbul baraj doluluk oranı %41 seviyelerinde olacaktır."
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

try:
    weather_by_city = fetch_all_accuweather()
    current_levels = {
        "İstanbul": round(float(ratio1_num), 2),
        "Bursa": round(float(ratio2_num), 2),
        "İzmir": round(float(ratio3_num), 2),
        "Ankara": round(float(ratio4_num), 2),
    }
    ai_note = deepseek_summary_week(current_levels, weather_by_city)
    if ai_note:
        base = tweet_text
        sep = " — "
        available = 270 - len(base) - len(sep)
        if available > 10:
            tweet_text = base + sep + ai_note[:available]
        else:
            tweet_text = base
    post_image_to_x(png_path, tweet_text)
    save_weather_json(weather_by_city)
except Exception as e:
    log(f"\033[93mAccuWeather/DeepSeek işlemi sırasında hata: {e}\033[0m")
