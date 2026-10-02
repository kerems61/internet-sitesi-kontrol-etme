from datetime import datetime
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests
import re

# ================= AYARLAR =================
SENDER_EMAIL = "keremsoylu503@gmail.com"
RECEIVER_EMAIL = "keremsoylu503@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
URL = "https://yyegm.meb.gov.tr/www/duyurular/kategori/2"

# TEST İÇİN BURAYI 16 YAPABİLİRSİN. (Normalde 1 kalmalı)
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
    print(f"E-posta gönderilirken hata oluştu: {e}")

def duyurulari_kontrol_et():
  bugun = datetime.now()
  bugun_str = bugun.strftime("%d.%m.%Y")

  try:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(URL, headers=headers, timeout=15)
    response.encoding = "utf-8"

    if response.status_code != 200:
      print("Siteye erişilemedi.")
      return

    soup = BeautifulSoup(response.text, "html.parser")
    yeni_duyuru_bulundu = False

    # Sayfadaki tüm satırları (tr) geziyoruz
    for tr in soup.find_all("tr"):
      tds = tr.find_all("td")
      
      if len(tds) >= 2:
        tarih_metni = tds[0].get_text(strip=True)
        
        # re.search ile metnin içinden sadece tarihi cımbızla çekiyoruz (boşluklara takılmamak için)
        tarih_eslesme = re.search(r"\d{2}[/.]\d{2}[/.]\d{4}", tarih_metni)
        
        if tarih_eslesme:
          # Bulunan tarihi güvenli bir şekilde alıp noktalı formata çeviriyoruz
          temiz_tarih_str = tarih_eslesme.group(0).replace("/", ".")
          
          try:
            duyuru_tarihi = datetime.strptime(temiz_tarih_str, "%d.%m.%Y")
          except ValueError:
            continue
          
          # Gün farkını hesaplıyoruz
          fark_gun = (bugun - duyuru_tarihi).days
          
          # EĞER DUYURU BELİRTİLEN GÜN ARALIĞINDAYSA:
          if 0 <= fark_gun <= KONTROL_GUN_SAYISI:
            baslik_etiketi = tds[1].find("a")
            
            if baslik_etiketi:
              baslik = baslik_etiketi.get_text(strip=True)
              link = baslik_etiketi.get("href", "")
              
              if not link.startswith("http"):
                link = "https://yyegm.meb.gov.tr/" + link.lstrip("/")
                
              konu = "🚨 YENİ DUYURU EKLENDİ!"
              icerik = (
                  f"Merhaba,\n\nMEB YYEGM sayfasında SON {KONTROL_GUN_SAYISI} GÜN İÇİNDE yayınlanan bir duyuru bulundu:\n\n"
                  f"📅 Tarih: {temiz_tarih_str}\n"
                  f"📌 Başlık: {baslik}\n"
                  f"🔗 Link: {link}\n\n"
                  f"Kontrol Edilen Zaman: {bugun_str}"
              )
              
              eposta_gonder(konu, icerik)
              yeni_duyuru_bulundu = True

    # Eğer şartları sağlayan hiçbir duyuru bulunamadıysa:
    if not yeni_duyuru_bulundu:
      konu = "ℹ️ MEB YYEGM Günlük Kontrol"
      icerik = (
          f"Bugün ({bugun_str}) saat 17.00 itibarıyla sayfa kontrol edildi.\n"
          f"Son {KONTROL_GUN_SAYISI} gün içinde yayınlanmış YENİ BİR DUYURU YOKTUR.\n\n"
          f"Adres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")

if __name__ == "__main__":
  duyurulari_kontrol_et()
