import os
import sys

# Kütüphaneleri kur
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

# TEST İÇİN 30. (Çalıştığını gördükten sonra otomasyon için 1 yapmayı unutma!)
KONTROL_GUN_SAYISI = 30  
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
    time.sleep(5)  # Tablonun yüklenmesi için bekle
    
    html_kaynagi = driver.page_source
    driver.quit()
  except Exception as e:
    print("Tarayıcı çalıştırılamadı:", e)
    return

  soup = BeautifulSoup(html_kaynagi, "html.parser")
  duyurular = []
  
  for tr in soup.find_all("tr"):
    tds = tr.find_all("td")
    if len(tds) >= 2:
      tarih_metni = tds[0].get_text(strip=True)
      match = re.search(r"(\d{2})[/.](\d{2})[/.](\d{4})", tarih_metni)
      
      if match:
        tarih_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
        baslik_etiketi = tds[1].find("a")
        
        if baslik_etiketi:
          baslik = baslik_etiketi.get_text(strip=True)
          link = baslik_etiketi.get("href", "")
          
          # "/icerik/" kısıtlamasını kaldırdık! Tabloda linki olan her şey duyurudur.
          if link:
            try:
              dt = datetime.strptime(tarih_str, "%d.%m.%Y")
              fark_gun = (bugun - dt).days
            except:
              fark_gun = 9999
            
            # Aynı duyuruyu listeye tekrar eklememek için
            if not any(d['link'] == link for d in duyurular):
              duyurular.append({
                  "baslik": baslik,
                  "link": link,
                  "tarih_str": tarih_str,
                  "fark_gun": fark_gun
              })

  # Sadece belirlediğimiz gün aralığında olanları filtrele
  yeni_duyurular = [d for d in duyurular if -2 <= d["fark_gun"] <= KONTROL_GUN_SAYISI]

  if yeni_duyurular:
    konu = f"🚨 YENİ DUYURU EKLENDİ! ({len(yeni_duyurular)} Adet)"
    icerik = f"Merhaba,\n\nMEB YYEGM Kategori-2 sayfasında {len(yeni_duyurular)} duyuru bulundu:\n\n"
    
    for i, d in enumerate(yeni_duyurular, 1):
      tam_link = d["link"] if d["link"].startswith("http") else "https://yyegm.meb.gov.tr/" + d["link"].lstrip("/")
      icerik += f"{i}) {d['baslik']}\n"
      icerik += f"   📅 {d['tarih_str']} | 🔗 {tam_link}\n\n"
      
    icerik += f"Kontrol Edilen Zaman: {bugun_str}"
    eposta_gonder(konu, icerik)
    
  else:
    konu = "ℹ️ MEB YYEGM Günlük Kontrol"
    icerik = (
        f"Bugün ({bugun_str}) saat 17.00 itibarıyla kontrol edildi.\n"
        f"Son {KONTROL_GUN_SAYISI} gün içinde eklenmiş YENİ BİR DUYURU YOKTUR.\n\n"
        f"Adres: {URL}"
    )
    eposta_gonder(konu, icerik)

if __name__ == "__main__":
  duyurulari_kontrol_et()
