"""
VD3350 Manager - Makine Preset Servisi
=========================================
Makine ayarları ve kağıt türleri yönetimi.
"""

from datetime import datetime
from typing import Optional
from database import db
from models import MakinePreseti, KagitTuru, RuloGecmisi, hesapla_rulo_metre


class PresetService:
    """Makine presetleri CRUD işlemleri."""

    def get_all(self) -> list[MakinePreseti]:
        """Tüm presetleri listeler."""
        rows = db.fetchall(
            "SELECT * FROM makine_presetleri ORDER BY malzeme_cinsi"
        )
        return [MakinePreseti.from_row(r) for r in rows]

    def get_by_malzeme(self, malzeme: str) -> Optional[MakinePreseti]:
        """Malzeme cinsine göre preset getirir."""
        row = db.fetchone(
            "SELECT * FROM makine_presetleri WHERE malzeme_cinsi = ?", (malzeme,)
        )
        return MakinePreseti.from_row(row) if row else None

    def save(self, preset: MakinePreseti) -> None:
        """Preset kaydeder veya günceller."""
        now = datetime.now().strftime("%Y-%m-%d")
        existing = self.get_by_malzeme(preset.malzeme_cinsi)
        if existing:
            db.execute(
                """UPDATE makine_presetleri
                   SET gramaj=?, kalinlik_micron=?, ideal_hiz=?,
                       bicak_basinci=?, ccd_hassasiyeti=?
                   WHERE malzeme_cinsi=?""",
                (
                    preset.gramaj,
                    preset.kalinlik_micron,
                    preset.ideal_hiz,
                    preset.bicak_basinci,
                    preset.ccd_hassasiyeti,
                    preset.malzeme_cinsi,
                ),
            )
        else:
            db.execute(
                """INSERT INTO makine_presetleri
                   (malzeme_cinsi, gramaj, kalinlik_micron, ideal_hiz,
                    bicak_basinci, ccd_hassasiyeti, olusturma_tarihi)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    preset.malzeme_cinsi,
                    preset.gramaj,
                    preset.kalinlik_micron,
                    preset.ideal_hiz,
                    preset.bicak_basinci,
                    preset.ccd_hassasiyeti,
                    now,
                ),
            )

    def delete(self, preset_id: int) -> None:
        """Preset siler."""
        db.execute("DELETE FROM makine_presetleri WHERE id = ?", (preset_id,))


class KagitTuruService:
    """Kağıt türleri CRUD işlemleri."""

    def get_all(self) -> list[KagitTuru]:
        """Tüm kağıt türlerini listeler."""
        rows = db.fetchall("SELECT * FROM kagit_turleri ORDER BY isim")
        return [KagitTuru.from_row(r) for r in rows]

    def get_names(self) -> list[str]:
        """Kağıt türü isimlerini listeler."""
        rows = db.fetchall("SELECT isim FROM kagit_turleri ORDER BY isim")
        return [r["isim"] for r in rows]

    def get_by_isim(self, isim: str) -> Optional[KagitTuru]:
        """İsme göre kağıt türü getirir."""
        row = db.fetchone("SELECT * FROM kagit_turleri WHERE isim = ?", (isim,))
        return KagitTuru.from_row(row) if row else None

    def save(self, kagit: KagitTuru) -> None:
        """Kağıt türü kaydeder veya günceller."""
        existing = self.get_by_isim(kagit.isim)
        if existing:
            db.execute(
                "UPDATE kagit_turleri SET kalinlik_micron=?, aciklama=? WHERE isim=?",
                (kagit.kalinlik_micron, kagit.aciklama, kagit.isim),
            )
        else:
            db.execute(
                "INSERT INTO kagit_turleri (isim, kalinlik_micron, aciklama) VALUES (?, ?, ?)",
                (kagit.isim, kagit.kalinlik_micron, kagit.aciklama),
            )

    def delete(self, kagit_id: int) -> None:
        """Kağıt türü siler."""
        db.execute("DELETE FROM kagit_turleri WHERE id = ?", (kagit_id,))


class RuloService:
    """Rulo hesaplama ve geçmiş işlemleri."""

    def hesapla_ve_kaydet(
        self, malzeme: str, cevre_cm: float, kalinlik_micron: float,
        ic_cap_cm: float = 7.6
    ) -> float:
        """Rulo metrajını hesaplar ve geçmişe kaydeder."""
        hesaplanan = hesapla_rulo_metre(cevre_cm, kalinlik_micron, ic_cap_cm)

        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            """INSERT INTO rulo_gecmisi
               (malzeme, cevre_cm, hesaplanan_metre, tarih)
               VALUES (?, ?, ?, ?)""",
            (malzeme, cevre_cm, hesaplanan, tarih),
        )
        return hesaplanan

    def get_gecmis(self, limit: int = 50) -> list[RuloGecmisi]:
        """Rulo geçmişini listeler."""
        rows = db.fetchall(
            "SELECT * FROM rulo_gecmisi ORDER BY tarih DESC LIMIT ?", (limit,)
        )
        return [RuloGecmisi.from_row(r) for r in rows]
