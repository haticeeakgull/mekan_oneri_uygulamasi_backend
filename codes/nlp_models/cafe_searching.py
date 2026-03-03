import torch
from transformers import AutoTokenizer, AutoModel
from supabase import create_client
import os
from dotenv import load_dotenv

# 1. Model ve Tokenizer Yükleme
load_dotenv()
model_yolu = "./models/bert_turkish/"
tokenizer = AutoTokenizer.from_pretrained(model_yolu)
model = AutoModel.from_pretrained(model_yolu)
model.eval()

# 2. Supabase Bağlantısı
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def akilli_kafe_ara(kullanici_sorgusu, secilen_ilce=None, secilen_vibe=None):
    # Vektörleştirme
    inputs = tokenizer(
        kullanici_sorgusu,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )
    with torch.no_grad():
        outputs = model(**inputs)
    sorgu_vektoru = outputs.last_hidden_state[0][0].tolist()

    # Kritik Kelimeler
    kritik_kelimeler = [
        "kitap",
        "sessiz",
        "sakin",
        "kütüphane",
        "alkol",
        "bira",
        "pub",
        "salaş",
        "vintage",
        "butik",
        "şık-premium",
        "ders-çalışmalık",
        "sosyal-canlı",
        "kafa-dinlemelik",
        "kafa-dağıtmalık",
        "oyun",
        "tavla",
    ]

    bulunan_anahtarlar = [k for k in kritik_kelimeler if k in kullanici_sorgusu.lower()]
    arama_metni = (
        " ".join(bulunan_anahtarlar) if bulunan_anahtarlar else kullanici_sorgusu
    )

    # RPC Çağrısı
    try:
        rpc_response = supabase.rpc(
            "kafe_ara_v5",
            {
                "query_embedding": sorgu_vektoru,
                "search_query": arama_metni,
                "p_ilce_adi": secilen_ilce,  # SQL'deki semt_adi filtresine gider
                "p_vibe_etiketi": secilen_vibe,
                "match_threshold": 0.1,
                "match_count": 5,
            },
        ).execute()
        return rpc_response.data
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None


# --- TEST VE YAZDIRMA ---


def sonuclari_yazdir(baslik, sonuclar):
    print(f"\n--- {baslik} ---")
    if sonuclar:
        for s in sonuclar:
            # semt_adi veya ilce_adi hangisini istersen yazdırabilirsin
            konum = s.get("semt_adi") or s.get("ilce_adi") or "Bilinmiyor"
            benzerlik = s.get("similarity", 0) * 100
            print(
                f"✅ Kafe: {s['kafe_adi']} - Konum: {konum} - Benzerlik: %{benzerlik:.2f}"
            )
            print(f"   Etiketler: {s.get('vibe_etiketleri')}")
    else:
        print("❌ Uygun bir mekan bulunamadı.")


# Senaryo Çalıştırmaları
if __name__ == "__main__":
    s1 = akilli_kafe_ara("sessiz kitap kafe")
    sonuclari_yazdir("Genel Arama", s1)

    s2 = akilli_kafe_ara("sakin güzel manzaralı salaş mekan", secilen_ilce="tunalı")
    sonuclari_yazdir("Tunalı Filtreli Arama", s2)

    s3 = akilli_kafe_ara("ders çalışmalık", secilen_vibe="salaş")
    sonuclari_yazdir("Salaş Vibes Araması", s3)
