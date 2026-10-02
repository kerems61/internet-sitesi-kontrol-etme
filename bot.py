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

    # Sayfadaki tüm bağlantıları tarayıp gerçek duyuru başlığı olabilecek metinleri bulalım
    bulunan_duyurular = []

    for a_tag in soup.find_all("a"):
      metin = a_tag.get_text(strip=True)
      link = a_tag.get("href", "")
      
      # Menü, anasayfa veya kısa/alakasız linkleri eleyelim, gerçek duyuru metinlerini alalım
      if (
          len(metin) > 20
          and "Anasayfa" not in metin
          and "Bakanlık" not in metin
          and "Mevzuat" not in metin
          and "İletişim" not in metin
      ):
        bulunan_duyurular.append((metin, link))

    if bulunan_duyurular:
      # Sayfadaki en güncel duyuru (listede ilk sırada yer alan)
      en_son_baslik, en_son_link = bulunan_duyurular[0]

      if en_son_link.startswith("/"):
        en_son_link = "https://yyegm.meb.gov.tr" + en_son_link
      elif not en_son_link.startswith("http"):
        en_son_link = URL

      konu = "📢 MEB YYEGM: En Son Duyuru"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM duyuru sayfasındaki en son duyuru başarıyla"
          f" yakalandı:\n\n📌 Duyuru Başlığı:\n{en_son_baslik}\n\n🔗 Bağlantı:"
          f" {en_son_link}\n\nKontrol Edilen Zaman: {bugun_tarih}"
      )
      eposta_gonder(konu, icerik)
    else:
      konu = "ℹ️ MEB YYEGM Günlük Kontrol"
      icerik = (
          f"Bugün ({bugun_tarih}) saat 17.00 itibarıyla sayfa kontrol edildi,"
          f" ancak duyuru metnine ulaşılamadı.\n\nAdres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")


if __name__ == "__main__":
  duyurulari_kontrol_et()
