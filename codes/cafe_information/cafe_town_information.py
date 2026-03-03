from geopy.geocoders import Nominatim
import pandas as pd
import time


df = pd.read_csv("csv_files/vektor_verili_adresli_kafeler_rows.csv")


geolocator = Nominatim(user_agent="mekan_uygulamasi")


def konum_dan_semt_bul(lat, lon):
    try:
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if not location:
            return "Bilinmiyor"

        address = location.raw.get("address", {})

        # 1. Öncelik: Mahalle/Semt (Örn: Üniversiteler Mahallesi)
        # 2. Öncelik: İlçe (Örn: Çankaya)
        # 3. Öncelik: Kasaba/Semt (Örn: Beşevler)

        semt = (
            address.get("city_district")
            or address.get("suburb")
            or address.get("neighbourhood")
        )
        ilce = address.get("town") or address.get("district") or address.get("city")

        # Eğer hem semt hem ilçe varsa "Üniversiteler (Çankaya)" formatında birleştirebilirsin
        # Ya da sadece ilçe istiyorsan ilce değişkenini döndür.
        if semt and ilce:
            return f"{semt} ({ilce})"
        return ilce or semt or "Bilinmiyor"

    except Exception as e:
        print(f"Hata oluştu: {e}")
        return "Hata"


ilceler = []
for index, row in df.iterrows():
    print(f"İşleniyor: {row['kafe_adi']}")
    ilce = konum_dan_semt_bul(row["latitude"], row["longitude"])
    ilceler.append(ilce)
    time.sleep(1.1)

df["ilce_adi"] = ilceler
df.to_csv("kafe_verileri_ilceli.csv", index=False)
