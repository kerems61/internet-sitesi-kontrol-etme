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

    en_son_baslik = ""
    en_son_link = ""

    # Sayfadaki tüm linkleri tarıyoruz
    for a in soup.find_all("a"):
      metin = a.get_text(strip=True)
      link = a.get("href", "")

      # Sadece 40 karakterden uzun olan metinleri dikkate al
      # Bu sayede Anasayfa, İletişim, Logolar gibi kısa bağlantılar otomatik elenir
      if len(metin) > 40 and link:
        en_son_baslik = metin
        en_son_link = link
        break  # 40 karakterden uzun ilk bağlantı, tablodaki en güncel duyurudur!

    if en_son_baslik:
      if en_son_link.startswith("/"):
        en_son_link = "https://yyegm.meb.gov.tr" + en_son_link
      elif not en_son_link.startswith("http"):
        en_son_link = "https://yyegm.meb.gov.tr/" + en_son_link

      konu = "📢 MEB YYEGM: Güncel Duyuru Kontrolü"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM sayfasındaki en üst sırada yer alan duyuru:\n\n"
          f"📌 Başlık:\n{en_son_baslik}\n\n"
          f"🔗 Bağlantı: {en_son_link}\n\n"
          f"Kontrol Edilen Zaman: {bugun_tarih}\n\n"
          f"(Not: Her gün saat 17:00'de gelen bu maildeki başlık, bir önceki günden farklıysa sayfaya yeni bir duyuru eklenmiş demektir.)"
      )
      eposta_gonder(konu, icerik)
    else:
      konu = "ℹ️ MEB YYEGM Günlük Kontrol"
      icerik = (
          f"Bugün ({bugun_tarih}) saat 17.00 itibarıyla sayfa kontrol edildi,"
          f" ancak 40 karakterden uzun bir duyuru metni bulunamadı.\n\nAdres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")


if __name__ == "__main__":
  duyurulari_kontrol_et()
