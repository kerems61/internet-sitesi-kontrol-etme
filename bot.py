from datetime import datetime
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import requests

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
  bugun_tarih = datetime.now().strftime("%d.%m.%Y")

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

    # Sayfadaki en güncel (en üstteki) duyuruyu ve bağlantısını çekelim
    # MEB sayfalarındaki duyuru başlıklarını ve linklerini barındıran etiketleri buluyoruz
    duyuru_elementi = None
    for a_tag in soup.find_all("a"):
      metin = a_tag.get_text(strip=True)
      # Genellikle duyuru başlıkları belirli bir uzunluktadır ve bağlantı içerir
      if len(metin) > 15:
        duyuru_elementi = a_tag
        break

    if duyuru_elementi:
      duyuru_basligi = duyuru_elementi.get_text(strip=True)
      duyuru_link = duyuru_elementi.get("href", "")

      # Eğer link göreceli (relative) ise tam adrese çevirelim
      if duyuru_link.startswith("/"):
        duyuru_link = "https://yyegm.meb.gov.tr" + duyuru_link
      elif not duyuru_link.startswith("http"):
        duyuru_link = URL

      konu = "📢 MEB YYEGM: En Son Duyuru Detayı"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM duyuru sayfası kontrol edildi. Sayfadaki en"
          f" son duyuru:\n\n📌 Başlık:\n{duyuru_basligi}\n\n🔗 Bağlantı:"
          f" {duyuru_link}\n\nKontrol Edilen Tarih: {bugun_tarih}"
      )
      eposta_gonder(konu, icerik)
    else:
      konu = "ℹ️ MEB YYEGM Günlük Kontrol"
      icerik = (
          f"Bugün ({bugun_tarih}) saat 17.00 itibarıyla sayfa kontrol edildi,"
          " ancak yeni bir duyuru öğesine ulaşılamadı.\n\nAdres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")


if __name__ == "__main__":
  duyurulari_kontrol_et()
