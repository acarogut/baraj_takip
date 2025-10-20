import time
from datetime import datetime
import os
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
post_image_to_x(png_path, tweet_text)
