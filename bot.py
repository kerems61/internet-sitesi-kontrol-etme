from datetime import datetime
import os
import re
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
  print(
      f"Kontrol edilen tarih: {bugun_tarih} - Adres taranıyor: {URL}"
  )

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
      print(f"Siteye erişilemedi. HTTP Kodu: {response.status_code}")
      return

    soup = BeautifulSoup(response.text, "html.parser")

    # Sayfadaki tüm metin içeriğini veya duyuru bloklarını tarayarak bugünün tarihini arayalım
    sayfa_metni = soup.get_text()

    # Regex ile sayfada bugünün tarihi (örn: 02.06.2026 veya benzeri formatlar) geçiyor mu diye bakıyoruz
    # Veya sayfadaki ilk duyuru başlığını ve tarihini yakalayalım
    yeni_duyurular = []

    # MEB sitelerindeki yaygın yapıları yakalamak için tüm bağlantıları ve metinleri tarayalım
    # Burada en güncel duyurunun tarihini kontrol edeceğiz
    duyuru_kutulari = soup.find_all(
        ["div", "li", "tr"],
        class_=lambda x: x and ("duyuru" in x.lower() or "news" in x.lower()),
    )

    # Eğer özel sınıf bulunamazsa genel bağlantı ve metin analizi yapalım
    bulundu = False
    ilgili_metin = ""

    for item in soup.find_all(["a", "div", "span"]):
      metin = item.get_text(strip=True)
      # Tarih formatını sayfada arıyoruz (GG.AA.YYYY)
      if bugun_tarih in metin:
        bulundu = True
        ilgili_metin = metin
        break

    if bulundu or bugun_tarih in sayfa_metni:
      # Alternatif olarak daha detaylı bilgi için sayfanın başlığını alalım
      konu = "🚨 MEB YYEGM: Bugün Yeni Duyuru Var!"
      icerik = (
          f"Merhaba,\n\nBugün ({bugun_tarih}) tarihli MEB YYEGM duyuru"
          " sayfasında yeni bir güncelleme veya bugünün tarihine ait bir ibare"
          f" saptandı.\n\nİlgili Detay:\n{ilgili_metin[:300]}\n\nKontrol Edilen"
          f" Adres:\n{URL}"
      )
      eposta_gonder(konu, icerik)
    else:
      konu = "ℹ️ MEB YYEGM Günlük Kontrol: Güncelleme Yok"
      icerik = (
          f"Bugün ({bugun_tarih}) saat 17.00 itibarıyla MEB YYEGM duyuru"
          " sayfası kontrol edildi. Tarih bazlı yeni bir duyuruya"
          " rastlanmadı, sistem güncel.\n\nKontrol Edilen Adres:\n{URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata oluştu: {e}")
    eposta_gonder(
        "⚠️️ MEB YYEGM Bot Hatası",
        f"Kontrol sırasında bir hata oluştu: {str(e)}",
    )


if __name__ == "__main__":
  duyurulari_kontrol_et()
