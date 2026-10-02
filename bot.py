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

# SADECE SON 1 GÜN İÇİNDE DUYURU VARSA HABER VERİR
KONTROL_GUN_SAYISI = 1  
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
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
  
  try:
    res = requests.get(URL, headers=headers, timeout=15)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, "html.parser")
  except Exception as e:
    print("Siteye erişilemedi:", e)
    return

  duyurular = []
  
  # Kategori sayfasındaki tüm linkleri tarıyoruz
  for a in soup.find_all("a"):
    link = a.get("href", "")
    baslik = a.get_text(strip=True)
    
    # MEB duyuruları her zaman /icerik/ uzantısına sahiptir ve başlıkları uzundur
    if "/icerik/" in link and len(baslik) > 15:
      # Linkin bulunduğu tablo satırını (tr) bulup içindeki tarihi çekiyoruz
      parent = a.find_parent("tr")
      if not parent:
          parent = a.find_parent("div")
          
      parent_text = parent.get_text(strip=True) if parent else ""
      match = re.search(r"(\d{2})[/.](\d{2})[/.](\d{4})", parent_text)
      
      tarih_str = ""
      fark_gun = 9999
      
      if match:
        tarih_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
        try:
          dt = datetime.strptime(tarih_str, "%d.%m.%Y")
          fark_gun = (bugun - dt).days
        except:
          pass
          
      # Aynı linki tekrar eklememek için kontrol
      if not any(d['link'] == link for d in duyurular):
        duyurular.append({
            "baslik": baslik,
            "link": link,
            "tarih_str": tarih_str,
            "fark_gun": fark_gun
        })

  yeni_duyuru_bulundu = False
  
  for d in duyurular:
    # Saat farklarından doğabilecek -1 veya -2 gün durumlarını da kapsar
    if -2 <= d["fark_gun"] <= KONTROL_GUN_SAYISI:
      tam_link = d["link"] if d["link"].startswith("http") else "https://yyegm.meb.gov.tr/" + d["link"].lstrip("/")
      konu = "🚨 YENİ DUYURU EKLENDİ!"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM Kategori-2 sayfasında YENİ BİR DUYURU yayınlandı!\n\n"
          f"📅 Tarih: {d['tarih_str']}\n"
          f"📌 Başlık: {d['baslik']}\n"
          f"🔗 Link: {tam_link}\n\n"
          f"Kontrol Edilen Zaman: {bugun_str}\n"
      )
      eposta_gonder(konu, icerik)
      yeni_duyuru_bulundu = True

  if not yeni_duyuru_bulundu:
    konu = "ℹ️ MEB YYEGM Günlük Kontrol"
    icerik = (
        f"Bugün ({bugun_str}) saat 17.00 itibarıyla sadece Kategori-2 sayfası kontrol edildi.\n"
        f"Son {KONTROL_GUN_SAYISI} gün içinde eklenmiş YENİ BİR DUYURU YOKTUR.\n\n"
        f"Adres: {URL}"
    )
    eposta_gonder(konu, icerik)

if __name__ == "__main__":
  duyurulari_kontrol_et()
