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
    # MEB güvenlik duvarını aşmak için gerçek bir tarayıcı gibi davranıyoruz
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    response = requests.get(URL, headers=headers, timeout=20)
    response.encoding = "utf-8"

    if response.status_code != 200:
      print(f"Siteye erişilemedi. Hata Kodu: {response.status_code}")
      return

    soup = BeautifulSoup(response.text, "html.parser")

    en_son_baslik = ""
    en_son_link = ""

    # Botun menü linklerine takılmaması için kara liste
    kara_liste = [
        "anasayfa", "bakanlık", "mevzuat", "iletişim", "müdürlük", 
        "hizmetler", "s.s.s", "eğitim", "mebbis", "e-okul", 
        "hakkımızda", "personel", "harita", "rss", "türk kültürü"
    ]

    # Sayfadaki tüm linkleri tarıyoruz
    for a in soup.find_all("a"):
      metin = a.get_text(strip=True)
      link = a.get("href", "")

      # Eğer metin 20 karakterden uzunsa ve kara listedeki kelimeleri içermiyorsa bu gerçek duyurudur!
      if len(metin) > 20 and link and link != "#":
        menuye_ait_mi = any(kelime in metin.lower() for kelime in kara_liste)
        
        if not menuye_ait_mi:
          en_son_baslik = metin
          en_son_link = link
          break

    if en_son_baslik:
      if en_son_link.startswith("/"):
        en_son_link = "https://yyegm.meb.gov.tr" + en_son_link
      elif not en_son_link.startswith("http"):
        en_son_link = "https://yyegm.meb.gov.tr/" + en_son_link

      konu = "📢 MEB YYEGM: En Son Duyuru Bulundu!"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM sayfasındaki güncel duyuru başarıyla çekildi:\n\n"
          f"📌 Başlık:\n{en_son_baslik}\n\n"
          f"🔗 Bağlantı: {en_son_link}\n\n"
          f"Kontrol Edilen Zaman: {bugun_tarih}"
      )
      eposta_gonder(konu, icerik)
    else:
      # EĞER BULAMAZSA BOTUN NE GÖRDÜĞÜNÜ BİZE MAİL ATACAK
      sayfa_basligi = soup.title.string if soup.title else "Başlık Bulunamadı"
      gorulen_metin = soup.get_text(strip=True)[:300] # Sayfadaki ilk 300 karakter
      
      konu = "⚠ MEB YYEGM: Duyuru Bulunamadı (Teşhis Raporu)"
      icerik = (
          f"Bugün ({bugun_tarih}) sayfa kontrol edildi ancak geçerli duyuru bulunamadı.\n\n"
          f"--- BOTUN GÖRDÜĞÜ SAYFA BİLGİLERİ ---\n"
          f"Sekme Başlığı: {sayfa_basligi}\n"
          f"Sayfadaki İlk Yazılar: {gorulen_metin}...\n\n"
          f"Not: Eğer yukarıdaki yazılarda 'Cloudflare', 'Güvenlik', veya 'Lütfen Bekleyin' yazıyorsa MEB botu engelliyordur. "
          f"Eğer sayfanın normal başlığı yazıyorsa tablo gizlidir.\n"
          f"Adres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")


if __name__ == "__main__":
  duyurulari_kontrol_et()
