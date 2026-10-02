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

# TEST İÇİN 16. (Çalıştığını görünce burayı 1 yapabilirsin)
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
    teshis_listesi = []

    # Yanlışlıkla menüleri almamak için kara liste
    kara_liste = ["ANASAYFA", "İLETİŞİM", "MEVZUAT", "BAKANLIK", "GENEL MÜDÜRLÜK", "YURT DIŞI", "HİZMETLER"]

    # Sayfadaki tüm linkleri tarıyoruz
    for a in soup.find_all("a"):
      metin = a.get_text(strip=True)
      link = a.get("href", "")

      # Eğer 25 karakterden uzunsa ve menü değilse kesinlikle duyurudur!
      if len(metin) > 25 and not any(k in metin.upper() for k in kara_liste):
        
        # Duyurunun etrafındaki (parent) HTML yapısını alıp tarihi arıyoruz
        parent = a.find_parent("tr")
        if not parent:
            parent = a.find_parent("div")
        
        parent_text = parent.get_text(strip=True) if parent else metin
        
        # Etrafındaki metnin içinden tarihi (\d{2}/\d{2}/\d{4}) cımbızla çekiyoruz
        tarih_eslesme = re.search(r"(\d{2}[/.]\d{2}[/.]\d{4})", parent_text)
        
        tarih_str = "Tarih Bulunamadı"
        fark_gun = -1
        
        if tarih_eslesme:
          tarih_str = tarih_eslesme.group(1).replace("/", ".")
          try:
            duyuru_tarihi = datetime.strptime(tarih_str, "%d.%m.%Y")
            fark_gun = (bugun - duyuru_tarihi).days
          except ValueError:
            pass
            
        # Teşhis raporu için botun bulduğu duyuruyu kaydediyoruz
        teshis_listesi.append(f"- {metin[:45]}... (Tarih: {tarih_str}, Fark: {fark_gun} gün)")

        # Eğer duyuru bizim belirlediğimiz gün aralığındaysa (0 ile 16 arası) MAİL AT!
        if 0 <= fark_gun <= KONTROL_GUN_SAYISI:
          if not link.startswith("http"):
            link = "https://yyegm.meb.gov.tr/" + link.lstrip("/")
            
          konu = "🚨 YENİ DUYURU EKLENDİ!"
          icerik = (
              f"Merhaba,\n\nMEB YYEGM sayfasında SON {KONTROL_GUN_SAYISI} GÜN İÇİNDE yayınlanan bir duyuru bulundu:\n\n"
              f"📅 Tarih: {tarih_str} ({fark_gun} gün önce)\n"
              f"📌 Başlık: {metin}\n"
              f"🔗 Link: {link}\n\n"
              f"Kontrol Edilen Zaman: {bugun_str}"
          )
          eposta_gonder(konu, icerik)
          yeni_duyuru_bulundu = True

    # Eğer şartları sağlayan yeni bir şey YOKSA, botun ne gördüğünü raporla:
    if not yeni_duyuru_bulundu:
      en_son_3 = "\n".join(teshis_listesi[:3]) if teshis_listesi else "Listede duyuru metni algılanamadı."
      konu = "ℹ️ MEB YYEGM Günlük Kontrol (Teşhis Raporlu)"
      icerik = (
          f"Bugün ({bugun_str}) saat 17.00 itibarıyla sayfa kontrol edildi.\n"
          f"Son {KONTROL_GUN_SAYISI} gün içinde yayınlanmış YENİ BİR DUYURU YOKTUR.\n\n"
          f"--- BOTUN SİTEDE GÖRDÜĞÜ EN SON DUYURULAR ---\n"
          f"{en_son_3}\n\n"
          f"Adres: {URL}"
      )
      eposta_gonder(konu, icerik)

  except Exception as e:
    print(f"Hata: {e}")

if __name__ == "__main__":
  duyurulari_kontrol_et()
