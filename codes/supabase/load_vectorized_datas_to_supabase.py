import os
import pandas as pd
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # CSV dosyasını oku
    df = pd.read_csv("kafe_verileri_ilceli.csv")
    print(f"{len(df)} mekan okunuyor...")
except Exception as e:
    print(f"Dosya okuma hatası: {e}")
    exit()

insert_list = []

for index, row in df.iterrows():
    try:
        # GÖRSELDEKİ BAŞLIKLARA GÖRE DÜZELTİLDİ:
        # 1. 'vektor' değil 'embedding' sütununa bakıyoruz
        if pd.isna(row["embedding"]):
            continue

        # Eğer embedding zaten listeyse (bazı pandas versiyonları otomatik çevirebilir)
        # direkt al, değilse json.loads kullan
        vektor = row["embedding"]
        if isinstance(vektor, str):
            vektor = json.loads(vektor)

        # 2. vibe_etiketleri dönüşümü
        etiketler = row["vibe_etiketleri"]
        if isinstance(etiketler, str):
            # CSV'deki format ['etiket1', 'etiket2'] şeklindeyse json.loads çalışır
            # Eğer sadece düz metinse .split(',') kullanmak gerekebilir
            etiketler = json.loads(etiketler.replace("'", '"'))
        elif pd.isna(etiketler):
            etiketler = []

        # VERİ SÖZLÜĞÜ (Görseldeki sütun isimleri ile birebir eşleşme)
        data = {
            "id": row["id"],  # Görselde ID var, eklemek iyi olur
            "kafe_adi": row["kafe_adi"],  # 'isim' değil 'kafe_adi'
            "ozellikler": (
                row["ozellikler"] if pd.notna(row["ozellikler"]) else ""
            ),  # 'yorumlar' değil 'ozellikler'
            "embedding": vektor,
            "latitude": row["latitude"],  # 'osm_lat' değil 'latitude'
            "longitude": row["longitude"],  # 'osm_lon' değil 'longitude'
            "vibe_etiketleri": etiketler,
            "ilce_adi": row["ilce_adi"] if pd.notna(row["ilce_adi"]) else "Bilinmiyor",
        }
        insert_list.append(data)
    except Exception as e:
        print(f"Satır {index} işlenirken hata: {e}")
        continue

# 2. Toplu Yükleme
try:
    if insert_list:
        # Tablo adını Supabase'de kontrol et (ilce_isimli_kafeler mi?)
        supabase.table("ilce_isimli_kafeler").insert(insert_list).execute()
        print(f"✅ {len(insert_list)} mekan başarıyla yüklendi!")
    else:
        print("⚠ Yüklenecek uygun veri bulunamadı.")
except Exception as e:
    print(f"❌ Supabase Yükleme Hatası: {e}")

print("İşlem tamam!")
