"""
VD3350 Manager - Örnek Veri Oluşturucu
========================================
Uygulamayı test etmek için örnek veriler oluşturur.
Çalıştırmak için: python seed_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db
from models import IsEmri, FireKaydi, BicakKafasi
from services.is_emri_service import IsEmriService
from services.fire_service import FireService
from services.bicak_service import BicakService


MUSTERILER = [
    "Anadolu Gıda A.Ş.", "Türk Ticaret Ltd.", "Mavi Market",
    "Güneş Tarım", "Akdeniz Pazarlama", "İstanbul Lojistik",
    "Yıldız Holding", "Boğaziçi Ambalaj", "Ege İhracat",
]

MALZEMELER = ["Kuşe", "PP Opak", "PP Şeffaf", "Termal", "PE", "Selefonlu"]

DURUMLAR = ["Bekliyor", "Tamamlandı", "Tamamlandı", "Tamamlandı", "Hatalı Kesim"]

FIRE_NEDENLERI = [
    "Sıyırma / Waste Koptu",
    "Kamera Pozlama Kaçırdı",
    "Bıçak Kesme Hatası",
    "Malzeme Kayması",
    "Rulo Defekti",
]


def generate_is_emirleri(gun: int = 30) -> None:
    """Son N gün için örnek iş emirleri oluşturur."""
    svc = IsEmriService()
    fire_svc = FireService()
    bicak_svc = BicakService()

    baslangic = datetime.now() - timedelta(days=gun)
    isim_sira = 1

    for g in range(gun):
        tarih = (baslangic + timedelta(days=g)).strftime("%Y-%m-%d")
        gun_is_sayisi = random.randint(2, 8)

        for _ in range(gun_is_sayisi):
            malzeme = random.choice(MALZEMELER)
            metraj = round(random.uniform(50, 800), 1)
            durum = random.choice(DURUMLAR)

            form_no = f"IE{tarih.replace('-', '')}{isim_sira:03d}"
            isim_sira += 1

            # Eğer aynı form no varsa atla
            mevcut = svc.get_by_form_no(form_no)
            if mevcut:
                continue

            emri = IsEmri(
                form_numarasi=form_no,
                tarih=tarih,
                musteri_adi=random.choice(MUSTERILER),
                malzeme_cinsi=malzeme,
                etiket_genisligi=round(random.uniform(30, 150), 1),
                etiket_yuksekligi=round(random.uniform(20, 100), 1),
                metraj=metraj,
                adet=random.randint(1000, 100000),
                durum=durum,
                aciklama="",
            )
            emri_id = svc.create(emri)

            # Tamamlanan işlere bıçak metre ekle
            if durum == "Tamamlandı":
                # Her kafalara metraj ekle (6 kafa)
                for kafa_no in range(1, 7):
                    bicak_svc.add_metre(kafa_no, metraj / 6)

            # Hatalı işlere fire ekle
            if durum == "Hatalı Kesim" or random.random() < 0.15:
                neden = random.choice(FIRE_NEDENLERI)
                kayit = FireKaydi(
                    form_numarasi=form_no,
                    tarih=tarih,
                    hatali_metre=round(random.uniform(1, 15), 2) if random.random() > 0.3 else None,
                    hatali_adet=random.randint(10, 500) if random.random() > 0.5 else None,
                    fire_nedeni=neden,
                    aciklama="Otomatik test verisi",
                )
                fire_svc.create(kayit)

    print(f"✅ {gun} günlük örnek veri oluşturuldu.")


if __name__ == "__main__":
    print("🌱 Örnek veri oluşturuluyor...")
    generate_is_emirleri(30)
    print("✅ Tamamlandı! Uygulamayı başlatabilirsiniz: python main.py")
