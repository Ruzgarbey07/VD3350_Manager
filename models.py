"""
VD3350 Manager - Data Models
==============================
Veri modelleri ve DTO (Data Transfer Object) sınıfları.
Veritabanı satırlarını Python nesnelerine dönüştürür.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import math


@dataclass
class IsEmri:
    """İş emri veri modeli."""

    id: Optional[int] = None
    form_numarasi: str = ""
    tarih: str = ""
    musteri_adi: str = ""
    malzeme_cinsi: str = ""
    etiket_genisligi: float = 0.0
    etiket_yuksekligi: float = 0.0
    metraj: float = 0.0
    adet: int = 0
    durum: str = "Bekliyor"
    aciklama: str = ""
    olusturulma_tarihi: str = ""
    guncellenme_tarihi: str = ""

    @classmethod
    def from_row(cls, row) -> "IsEmri":
        """SQLite satırından IsEmri nesnesi oluşturur."""
        return cls(
            id=row["id"],
            form_numarasi=row["form_numarasi"],
            tarih=row["tarih"],
            musteri_adi=row["musteri_adi"],
            malzeme_cinsi=row["malzeme_cinsi"],
            etiket_genisligi=row["etiket_genisligi"],
            etiket_yuksekligi=row["etiket_yuksekligi"],
            metraj=row["metraj"],
            adet=row["adet"],
            durum=row["durum"],
            aciklama=row["aciklama"] or "",
            olusturulma_tarihi=row["olusturulma_tarihi"],
            guncellenme_tarihi=row["guncellenme_tarihi"],
        )


@dataclass
class FireKaydi:
    """Fire ve hata kaydı veri modeli."""

    id: Optional[int] = None
    form_numarasi: Optional[str] = None
    tarih: str = ""
    hatali_metre: Optional[float] = None
    hatali_adet: Optional[int] = None
    fire_nedeni: str = ""
    aciklama: str = ""

    @classmethod
    def from_row(cls, row) -> "FireKaydi":
        """SQLite satırından FireKaydi nesnesi oluşturur."""
        return cls(
            id=row["id"],
            form_numarasi=row["form_numarasi"],
            tarih=row["tarih"],
            hatali_metre=row["hatali_metre"],
            hatali_adet=row["hatali_adet"],
            fire_nedeni=row["fire_nedeni"] or "",
            aciklama=row["aciklama"] or "",
        )


@dataclass
class MakinePreseti:
    """Makine preset veri modeli."""

    id: Optional[int] = None
    malzeme_cinsi: str = ""
    gramaj: float = 0.0
    kalinlik_micron: float = 0.0
    ideal_hiz: float = 0.0
    bicak_basinci: float = 0.0
    ccd_hassasiyeti: float = 0.0
    olusturma_tarihi: str = ""

    @classmethod
    def from_row(cls, row) -> "MakinePreseti":
        """SQLite satırından MakinePreseti nesnesi oluşturur."""
        return cls(
            id=row["id"],
            malzeme_cinsi=row["malzeme_cinsi"],
            gramaj=row["gramaj"] or 0.0,
            kalinlik_micron=row["kalinlik_micron"] or 0.0,
            ideal_hiz=row["ideal_hiz"] or 0.0,
            bicak_basinci=row["bicak_basinci"] or 0.0,
            ccd_hassasiyeti=row["ccd_hassasiyeti"] or 0.0,
            olusturma_tarihi=row["olusturma_tarihi"],
        )


@dataclass
class BicakKafasi:
    """Bıçak kafası veri modeli."""

    id: Optional[int] = None
    kafa_no: int = 0
    takilan_uc_tarihi: str = ""
    toplam_kesilen_metre: float = 0.0
    tahmini_omur: float = 35000.0
    durum: str = "Normal"

    @classmethod
    def from_row(cls, row) -> "BicakKafasi":
        """SQLite satırından BicakKafasi nesnesi oluşturur."""
        return cls(
            id=row["id"],
            kafa_no=row["kafa_no"],
            takilan_uc_tarihi=row["takilan_uc_tarihi"],
            toplam_kesilen_metre=row["toplam_kesilen_metre"],
            tahmini_omur=row["tahmini_omur"],
            durum=row["durum"],
        )

    @property
    def kullanim_yuzdesi(self) -> float:
        """Kullanım yüzdesini hesaplar (0-100)."""
        if self.tahmini_omur <= 0:
            return 100.0
        return min(100.0, (self.toplam_kesilen_metre / self.tahmini_omur) * 100)

    @property
    def kalan_yuzdesi(self) -> float:
        """Kalan ömür yüzdesini hesaplar (0-100)."""
        return max(0.0, 100.0 - self.kullanim_yuzdesi)

    @property
    def durum_rengi(self) -> str:
        """Kalan yüzdeye göre durum rengini döner."""
        kalan = self.kalan_yuzdesi
        if kalan >= 60:
            return "#10b981"  # Yeşil
        elif kalan >= 40:
            return "#f59e0b"  # Sarı
        elif kalan >= 20:
            return "#f97316"  # Turuncu
        else:
            return "#ef4444"  # Kırmızı


@dataclass
class KagitTuru:
    """Kağıt türü veri modeli."""

    id: Optional[int] = None
    isim: str = ""
    kalinlik_micron: float = 0.0
    aciklama: str = ""

    @classmethod
    def from_row(cls, row) -> "KagitTuru":
        """SQLite satırından KagitTuru nesnesi oluşturur."""
        return cls(
            id=row["id"],
            isim=row["isim"],
            kalinlik_micron=row["kalinlik_micron"],
            aciklama=row["aciklama"] or "",
        )


@dataclass
class RuloGecmisi:
    """Rulo geçmişi veri modeli."""

    id: Optional[int] = None
    malzeme: str = ""
    baslangic_metre: Optional[float] = None
    kalan_metre: Optional[float] = None
    cevre_cm: float = 0.0
    hesaplanan_metre: float = 0.0
    tarih: str = ""

    @classmethod
    def from_row(cls, row) -> "RuloGecmisi":
        """SQLite satırından RuloGecmisi nesnesi oluşturur."""
        return cls(
            id=row["id"],
            malzeme=row["malzeme"],
            baslangic_metre=row["baslangic_metre"],
            kalan_metre=row["kalan_metre"],
            cevre_cm=row["cevre_cm"],
            hesaplanan_metre=row["hesaplanan_metre"],
            tarih=row["tarih"],
        )


def hesapla_rulo_metre(cevre_cm: float, kalinlik_micron: float, ic_cap_cm: float = 7.6) -> float:
    """
    Rulo çevresinden kalan metreyi hesaplar.
    
    Formül: π × (D_dış² - D_iç²) / (4 × kalınlık)
    
    Args:
        cevre_cm: Rulonun dış çevresi (cm)
        kalinlik_micron: Malzeme kalınlığı (mikron)
        ic_cap_cm: İç çap (cm), varsayılan 7.6 cm (3 inç)
    
    Returns:
        Yaklaşık metre miktarı
    """
    if cevre_cm <= 0 or kalinlik_micron <= 0:
        return 0.0
    
    # Çevreden dış çapı hesapla
    dis_cap_cm = cevre_cm / math.pi
    
    # İç çap
    ic_cap = ic_cap_cm
    
    # Kalınlığı cm'ye çevir (1 mikron = 0.0001 cm)
    kalinlik_cm = kalinlik_micron * 0.0001
    
    # Sarım uzunluğu formülü
    metre = math.pi * (dis_cap_cm ** 2 - ic_cap ** 2) / (4 * kalinlik_cm * 100)
    
    return max(0.0, metre)
