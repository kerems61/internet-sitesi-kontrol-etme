from datetime import datetime
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests
import re

# Ayarlar
SENDER_EMAIL = "keremsoylu503@gmail.com"
RECEIVER_EMAIL = "keremsoylu503@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
URL = "https://yyegm.meb.gov.tr/www/duyurular/kategori/2"


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
      
      # Eğer satırda en az 2 hücre (Tarih ve Başlık) varsa
      if len(tds) >= 2:
        tarih_metni = tds[0].get_text(strip=True)
        
        # SADECE "17.09.2026" veya "17/09/2026" gibi tarih olan hücreleri kabul et
        if re.match(r"\d{2}[/.]\d{2}[/.]\d{4}", tarih_metni):
          
          # Tarih formatını hesaplanabilir hale getir
          tarih_temiz = tarih_metni.replace("/", ".")
          try:
            duyuru_tarihi = datetime.strptime(tarih_temiz, "%d.%m.%Y")
          except ValueError:
            continue
          
          # Bugün ile duyuru tarihi arasındaki gün farkını hesapla
          fark_gun = (bugun - duyuru_tarihi).days
          
          # EĞER DUYURU SON 1 GÜN İÇİNDE YAYINLANMIŞSA:
          if fark_gun <= 30 and fark_gun >= 0:
            baslik_etiketi = tds[1].find("a")
            
            if baslik_etiketi:
              baslik = baslik_etiketi.get_text(strip=True)
              link = baslik_etiketi.get("href", "")
              
              if not link.startswith("http"):
                link = "https://yyegm.meb.gov.tr/" + link.lstrip("/")
                
              konu = "🚨 YENİ DUYURU EKLENDİ!"
              icerik = (
                  f"Merhaba,\n\nMEB YYEGM sayfasında SON 1 GÜN İÇİNDE yeni bir duyuru yayınlandı:\n\n"
                  f"📅 Tarih: {tarih_metni}\n"
                  f"📌 Başlık: {baslik}\n"
                  f"🔗 Link: {link}\n\n"
                  f"Kontrol Edilen Zaman: {bugun_str}"
              )
              
              # Şartı sağlayan her duyuru için ayrı ayrı mail atar
              eposta_gonder(konu, icerik)
              yeni_duyuru_bulundu = True

    # Eğer sayfa tarandı ve son 1 güne ait HİÇBİR duyuru bulunamadıysa:
    if not yeni_duyuru_bulundu:
      konu = "ℹ️ MEB YYEGM Günlük Kontrol"
      icerik = (
          f"Bugün ({bugun_str}) saat 17.00 itibarıyla sayfa kontrol edildi.\n"
          f"Son 1 gün içinde yayınlanmış YENİ BİR DUYURU YOKTUR.\n\n"
          f"Adres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")


if __name__ == "__main__":
  duyurulari_kontrol_et()
