from datetime import datetime
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import requests
import re

# ================= AYARLAR =================
SENDER_EMAIL = "keremsoylu503@gmail.com"
RECEIVER_EMAIL = "keremsoylu503@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# TEST ETMEK İÇİN BURAYI 16 YAP. ÇALIŞTIĞINI GÖRÜNCE 1'E DÜŞÜR.
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
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
  
  duyurular = []
  
  # 1. YÖNTEM: RSS Arka Kapısı (JS gerektirmez, doğrudan saf veriyi çeker)
  try:
    res = requests.get("https://yyegm.meb.gov.tr/www/rss.php", headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    for item in soup.find_all("item"):
      baslik = item.find("title").get_text(strip=True) if item.find("title") else ""
      link = item.find("link").get_text(strip=True) if item.find("link") else ""
      tarih = item.find("pubdate").get_text(strip=True) if item.find("pubdate") else ""
      if baslik and link:
        duyurular.append({"baslik": baslik, "link": link, "tarih_metni": tarih, "kaynak": "RSS Verisi"})
  except:
    pass
      
  # 2. YÖNTEM: Anasayfa (RSS çalışmazsa, ana sayfadaki "Duyurular" sekmesini tara)
  try:
    res = requests.get("https://yyegm.meb.gov.tr/", headers=headers, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    for a in soup.find_all("a"):
      link = a.get("href", "")
      baslik = a.get_text(strip=True)
      # MEB'de gerçek duyurular her zaman /icerik/ uzantısına sahiptir
      if "/icerik/" in link and len(baslik) > 15:
        parent = a.find_parent()
        tarih = parent.get_text(strip=True) if parent else ""
        duyurular.append({"baslik": baslik, "link": link, "tarih_metni": tarih, "kaynak": "Anasayfa İçeriği"})
  except:
    pass
      
  yeni_duyuru_bulundu = False
  gonderilen_linkler = set()
  teshis_log = []
  
  for d in duyurular:
    baslik = d["baslik"]
    link = d["link"]
    tarih_metni = d["tarih_metni"]
    kaynak = d["kaynak"]
    
    if not link.startswith("http"):
      link = "https://yyegm.meb.gov.tr/" + link.lstrip("/")
        
    # Aynı duyuruyu (hem RSS hem anasayfada varsa) 2 kez atmamak için engelleme
    if link in gonderilen_linkler:
      continue
        
    fark_gun = -1
    tarih_str = "Çözülemedi"
    
    # Tarihi hesapla (RSS standardı RFC 822 formatı)
    try:
      dt = parsedate_to_datetime(tarih_metni)
      dt = dt.replace(tzinfo=None)
      tarih_str = dt.strftime("%d.%m.%Y")
      fark_gun = (bugun - dt).days
    except:
      # Eğer RSS değilse, metin içindeki "17.09.2026" kalıbını bul
      match = re.search(r"(\d{2})[/.](\d{2})[/.](\d{4})", tarih_metni)
      if match:
        tarih_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
        try:
          dt = datetime.strptime(tarih_str, "%d.%m.%Y")
          fark_gun = (bugun - dt).days
        except:
          pass
    
    teshis_log.append(f"[{kaynak}] {baslik[:35]}... (Fark: {fark_gun} gün)")
    
    # BELİRLENEN GÜN ARALIĞINDA (Örn: 16 gün) DUYURU VARSA MAİL AT:
    if 0 <= fark_gun <= KONTROL_GUN_SAYISI:
      konu = "🚨 YENİ DUYURU EKLENDİ!"
      icerik = (
          f"Merhaba,\n\nMEB YYEGM sayfasında SON {KONTROL_GUN_SAYISI} GÜN İÇİNDE yayınlanan bir duyuru yakalandı!\n\n"
          f"📅 Tarih: {tarih_str} ({fark_gun} gün önce)\n"
          f"📌 Başlık: {baslik}\n"
          f"🔗 Link: {link}\n\n"
          f"Kontrol Edilen Zaman: {bugun_str}\n"
          f"Veri Kaynağı: {kaynak}"
      )
      eposta_gonder(konu, icerik)
      yeni_duyuru_bulundu = True
      gonderilen_linkler.add(link)
      
  # EĞER HİÇ YENİ DUYURU YOKSA SADECE BİLGİ MAİLİ AT (TEST İÇİN LOGLARIYLA BİRLİKTE):
  if not yeni_duyuru_bulundu:
    log_ozet = "\n".join(teshis_log[:5]) if teshis_log else "Hiçbir kaynaktan duyuru verisi alınamadı."
    konu = "ℹ️ MEB YYEGM Günlük Kontrol"
    icerik = (
        f"Bugün ({bugun_str}) saat 17.00 itibarıyla kontrol sağlandı.\n"
        f"Son {KONTROL_GUN_SAYISI} gün içinde yayınlanmış YENİ BİR DUYURU YOKTUR.\n\n"
        f"--- BOTUN ARKA KAPIDAN OKUDUĞU EN GÜNCEL KAYITLAR ---\n"
        f"{log_ozet}\n"
    )
    eposta_gonder(konu, icerik)

if __name__ == "__main__":
  duyurulari_kontrol_et()
