import json
from supabase import create_client
from dotenv import load_dotenv
import os


load_dotenv()
# 1. Supabase Bilgilerini Gir
# Supabase Panel -> Project Settings -> API kısmından alabilirsin
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Eski JSON dosyasını oku
# Dosya adının doğru olduğundan emin ol
try:
    with open(
        "json_files/vektorlu_mekan_verisi_owner_yorumlarindan_temizlenmis_ankara.json",
        "r",
        encoding="utf-8",
    ) as f:
        eski_veriler = json.load(f)
except FileNotFoundError:
    print(
        "Hata: 'vektorlu_mekan_verisi_owner_yorumlarindan_temizlenmis_ankara.json' dosyası bulunamadı!"
    )
    exit()

print(f"Toplam {len(eski_veriler)} adet kafe taranıyor...\n")

for kafe in eski_veriler:
    kafe_adi = kafe.get("isim", "Bilinmeyen Kafe")

    # Koordinatları al ve float'a çevir
    try:
        raw_lat = float(kafe.get("osm_lat", 0))
        raw_lon = float(kafe.get("osm_lon", 0))
    except (TypeError, ValueError):
        print(f"Sıfır veya hatalı koordinat: {kafe_adi}")
        continue

    # 6 basamağa yuvarla
    lat = round(raw_lat, 6)
    lon = round(raw_lon, 6)

    yorum_listesi = kafe.get("yorumlar", [])

    # 3. Supabase'de koordinat aralığı ile kafeyi bul (Toleranslı arama)
    # 0.00001 tolerans yaklaşık 1 metrelik bir yanılma payıdır
    tol = 0.00001

    try:
        response = (
            supabase.table("ilce_isimli_kafeler")
            .select("id")
            .gte("latitude", lat - tol)
            .lte("latitude", lat + tol)
            .gte("longitude", lon - tol)
            .lte("longitude", lon + tol)
            .execute()
        )

        if response.data:
            cafe_id = response.data[0]["id"]
            print(f"✔️ Eşleşme: {kafe_adi} (ID: {cafe_id})")

            # A. Önce o kafeye ait eski yorumları temizle
            supabase.table("cafe_yorumlar").delete().eq("cafe_id", cafe_id).execute()

            # B. Yeni yorumları tek tek ekle
            eklenen_sayisi = 0
            for yorum_metni in yorum_listesi:
                # Metin temizliği: Gereksiz boşlukları ve satır sonlarını sil
                temiz_yorum = " ".join(str(yorum_metni).split())

                # Kalite kontrol: 5 karakterden kısa yorumları atla
                if len(temiz_yorum) > 5:
                    supabase.table("cafe_yorumlar").insert(
                        {
                            "cafe_id": cafe_id,
                            "kullanici_adi": "Sistem Arşivi",
                            "yorum_metni": temiz_yorum,
                        }
                    ).execute()
                    eklenen_sayisi += 1

            print(f"   -> {eklenen_sayisi} adet temiz yorum aktarıldı.")
        else:
            print(f"Bulunamadı: {kafe_adi} ({lat}, {lon})")

    except Exception as e:
        print(f"⚠️ Hata oluştu ({kafe_adi}): {e}")

print("\nİşlem başarıyla tamamlandı!")
