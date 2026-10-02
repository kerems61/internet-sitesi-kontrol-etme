import os
import sys

# 1. Aşama: Gerekli kütüphaneleri otomatik yükle (GitHub Actions için)
print("Sistem hazırlanıyor, kütüphaneler kuruluyor...")
os.system(f"{sys.executable} -m pip install -q selenium webdriver-manager beautifulsoup4")

from datetime import datetime
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

# ================= AYARLAR =================
SENDER_EMAIL = "keremsoylu503@gmail.com"
RECEIVER_EMAIL = "keremsoylu503@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
URL = "https://yyegm.meb.gov.tr/www/duyurular/kategori/2"

# TEST İÇİN 16 YAPTIK (Çalıştığını görünce burayı 1 yapabilirsin)
KONTROL_GUN_SAYISI = 16  
# ===========================================

def eposta_gonder(konu, icerik):
  try:
    sifre = os.environ.get("GMAIL_SIFRE")
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = Header(konu, "utf-8")
    msg.attach(MIMEText(icerik, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
      server.starttls()
      server.login(SENDER_EMAIL, sifre)
      server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print("E-posta başarıyla gönderildi.")
  except Exception as e:
    print(f"Hata: {e}")

def duyurulari_kontrol_et():
  bugun = datetime.now()
  bugun_str = bugun.strftime("%d.%m.%Y")
  
  print("Görünmez tarayıcı (Headless Chrome) başlatılıyor...")
  
  # Görünmez (Headless) Chrome Ayarları
  chrome_options = Options()
  chrome_options.add_argument("--headless")
  chrome_options.add_argument("--no-sandbox")
  chrome_options.add_argument("--disable-dev-shm-usage")
  chrome_options.add_argument("--window-size=1920,1080")
  chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
  
  try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    print("MEB sayfasına bağlanılıyor...")
    driver.get(URL)
    
    # JavaScript tablosunun yüklenmesi için 5 saniye bekle! (KRİTİK NOKTA)
    print("Sayfanın ve tabloların yüklenmesi bekleniyor...")
    time.sleep(5)
    
    # Yüklenmiş tam sayfa kodunu al
    html_kaynagi = driver.page_source
    driver.quit()
  except Exception as e:
    print("Tarayıcı çalıştırılamadı:", e)
    return

  soup = BeautifulSoup(html_kaynagi, "html.parser")
  duyurular = []
  
  # SADECE ve SADECE tablo satırlarını (tr) tarıyoruz
  for tr in soup.find_all("tr"):
    tds = tr.find_all("td")
    if len(tds) >= 2:
      tarih_metni = tds[0].get_text(strip=True)
      
      # İlk hücrede tarih var mı kontrol et
      match = re.search(r"(\d{2})[/.](\d{2})[/.](\d{4})", tarih_metni)
      if match:
        tarih_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
        baslik_etiketi = tds[1].find("a")
        
        if baslik_etiketi:
          baslik = baslik_etiketi.get_text(strip=True)
          link = baslik_etiketi.get("href", "")
          
          if "/icerik/" in link:  # Gerçek bir MEB duyurusu olduğunu teyit ediyoruz
            try:
              dt = datetime.strptime(tarih_str, "%d.%m.%Y")
              fark_gun = (bugun - dt).days
            except:
              fark_gun = 9999
            
            duyurular.append({
                "baslik": baslik,
                "link": link,
                "tarih_str": tarih_str,
                "fark_gun": fark_gun
            })

  yeni_duyuru_bulundu = False
  
  for d in duyurular:
    if -2 <= d["fark_gun"] <= KONTROL_GUN_SAYISI:
      tam_link = d["link"] if d["link"].startswith("http") else "https://yyegm.meb.gov.tr/" + d["link"].lstrip("/")
      konu = "🚨 MEB KATEGORİ-2 YENİ DUYURU!"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM Kategori-2 sayfasındaki TABLODA yeni bir duyuru yakalandı!\n\n"
          f"📅 Tarih: {d['tarih_str']} (Sistem Farkı: {d['fark_gun']} gün)\n"
          f"📌 Başlık: {d['baslik']}\n"
          f"🔗 Link: {tam_link}\n\n"
          f"Kontrol Edilen Zaman: {bugun_str}\n"
      )
      eposta_gonder(konu, icerik)
      yeni_duyuru_bulundu = True

  if not yeni_duyuru_bulundu:
    # Duyuru bulamazsa botun okuduğu ilk satırı kanıt olarak gönderelim
    ilk_kayit = duyurular[0] if duyurular else None
    ek_bilgi = f"\n(Botun gördüğü son duyuru: {ilk_kayit['tarih_str']} - {ilk_kayit['baslik']})" if ilk_kayit else "\n(Tabloda veri okunamadı!)"
    
    konu = "ℹ️ MEB YYEGM Günlük Kontrol"
    icerik = (
        f"Bugün ({bugun_str}) saat 17.00 itibarıyla görünmez tarayıcı ile tablo kontrol edildi.\n"
        f"Son {KONTROL_GUN_SAYISI} gün içinde eklenmiş YENİ BİR DUYURU YOKTUR.\n{ek_bilgi}\n\n"
        f"Adres: {URL}"
    )
    eposta_gonder(konu, icerik)

if __name__ == "__main__":
  duyurulari_kontrol_et()
