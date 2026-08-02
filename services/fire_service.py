"""
VD3350 Manager - Fire Servisi
================================
Fire ve hata kayıtları ile ilgili iş mantığı.
"""

from datetime import datetime
from typing import Optional
from database import db
from models import FireKaydi


class FireService:
    """Fire ve hata kayıtları CRUD işlemleri."""

    def create(self, kayit: FireKaydi) -> int:
        """Yeni fire kaydı oluşturur."""
        cursor = db.execute(
            """INSERT INTO fire_ve_hatalar
               (form_numarasi, tarih, hatali_metre, hatali_adet, fire_nedeni, aciklama)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                kayit.form_numarasi,
                kayit.tarih,
                kayit.hatali_metre,
                kayit.hatali_adet,
                kayit.fire_nedeni,
                kayit.aciklama,
            ),
        )
        return cursor.lastrowid  # type: ignore

    def get_all(self) -> list[FireKaydi]:
        """Tüm fire kayıtlarını listeler."""
        rows = db.fetchall(
            "SELECT * FROM fire_ve_hatalar ORDER BY tarih DESC, id DESC"
        )
        return [FireKaydi.from_row(r) for r in rows]

    def get_by_form_no(self, form_no: str) -> list[FireKaydi]:
        """Form numarasına göre fire kayıtlarını getirir."""
        rows = db.fetchall(
            "SELECT * FROM fire_ve_hatalar WHERE form_numarasi = ? ORDER BY id DESC",
            (form_no,),
        )
        return [FireKaydi.from_row(r) for r in rows]

    def get_son_30_gun_fire(self) -> list[dict]:
        """Son 30 günün fire verilerini döner."""
        rows = db.fetchall(
            """SELECT tarih, SUM(hatali_metre) as toplam_fire, COUNT(*) as kayit_sayisi
               FROM fire_ve_hatalar
               WHERE tarih >= date('now', '-30 days')
               GROUP BY tarih
               ORDER BY tarih"""
        )
        return [dict(r) for r in rows]

    def get_fire_nedenleri(self) -> list[dict]:
        """Fire nedenlerinin dağılımını döner."""
        rows = db.fetchall(
            """SELECT fire_nedeni, COUNT(*) as adet, SUM(hatali_metre) as toplam_metre
               FROM fire_ve_hatalar
               WHERE fire_nedeni IS NOT NULL AND fire_nedeni != ''
               GROUP BY fire_nedeni
               ORDER BY adet DESC"""
        )
        return [dict(r) for r in rows]

    def delete(self, kayit_id: int) -> None:
        """Fire kaydını siler."""
        db.execute("DELETE FROM fire_ve_hatalar WHERE id = ?", (kayit_id,))

    def add_waste_fire(self, form_no: Optional[str], metre: float = 2.0) -> None:
        """Sıyırma/waste fire ekler."""
        kayit = FireKaydi(
            form_numarasi=form_no,
            tarih=datetime.now().strftime("%Y-%m-%d"),
            hatali_metre=metre,
            hatali_adet=None,
            fire_nedeni="Sıyırma / Waste Koptu",
            aciklama="Otomatik eklendi - Operatör bildirimi",
        )
        self.create(kayit)

    def add_kamera_fire(self, form_no: Optional[str]) -> None:
        """Kamera pozlama hatası fire ekler."""
        kayit = FireKaydi(
            form_numarasi=form_no,
            tarih=datetime.now().strftime("%Y-%m-%d"),
            hatali_metre=None,
            hatali_adet=None,
            fire_nedeni="Kamera Pozlama Kaçırdı",
            aciklama="Otomatik eklendi - Kamera hatası",
        )
        self.create(kayit)
