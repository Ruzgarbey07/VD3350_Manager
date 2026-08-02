"""
VD3350 Manager - Bıçak Takip Servisi
=======================================
Bıçak kafaları yönetimi ve ömür hesaplama.
"""

from datetime import datetime
from typing import Optional
from database import db
from models import BicakKafasi


class BicakService:
    """Bıçak kafası takip ve yönetim işlemleri."""

    def get_all(self) -> list[BicakKafasi]:
        """Tüm bıçak kafalarını listeler."""
        rows = db.fetchall("SELECT * FROM bicak_kafalari ORDER BY kafa_no")
        return [BicakKafasi.from_row(r) for r in rows]

    def get_by_kafa_no(self, kafa_no: int) -> Optional[BicakKafasi]:
        """Kafa numarasına göre bıçak kafasını getirir."""
        row = db.fetchone(
            "SELECT * FROM bicak_kafalari WHERE kafa_no = ?", (kafa_no,)
        )
        return BicakKafasi.from_row(row) if row else None

    def reset_kafa(self, kafa_no: int) -> None:
        """Bıçak kafasını sıfırlar (yeni uç takıldığında)."""
        now = datetime.now().strftime("%Y-%m-%d")
        db.execute(
            """UPDATE bicak_kafalari
               SET takilan_uc_tarihi = ?, toplam_kesilen_metre = 0, durum = 'Normal'
               WHERE kafa_no = ?""",
            (now, kafa_no),
        )

    def add_metre(self, kafa_no: int, metre: float) -> None:
        """Kesilen metreyi kafaya ekler."""
        db.execute(
            """UPDATE bicak_kafalari
               SET toplam_kesilen_metre = toplam_kesilen_metre + ?
               WHERE kafa_no = ?""",
            (metre, kafa_no),
        )
        self._update_durum(kafa_no)

    def add_all_kafalar(self, metre: float) -> None:
        """Tüm aktif kafalara metre ekler (makine çalıştığında)."""
        for kafa_no in range(1, 7):
            self.add_metre(kafa_no, metre)

    def _update_durum(self, kafa_no: int) -> None:
        """Kafanın durumunu kalan ömre göre günceller."""
        kafa = self.get_by_kafa_no(kafa_no)
        if not kafa:
            return

        kalan = kafa.kalan_yuzdesi
        if kalan >= 60:
            durum = "Normal"
        elif kalan >= 40:
            durum = "İyi"
        elif kalan >= 20:
            durum = "Uyarı"
        else:
            durum = "Kritik"

        db.execute(
            "UPDATE bicak_kafalari SET durum = ? WHERE kafa_no = ?",
            (durum, kafa_no),
        )

    def update_tahmini_omur(self, kafa_no: int, yeni_omur: float) -> None:
        """Kafanın tahmini ömrünü günceller."""
        db.execute(
            "UPDATE bicak_kafalari SET tahmini_omur = ? WHERE kafa_no = ?",
            (yeni_omur, kafa_no),
        )

    def get_kritik_kafalar(self) -> list[BicakKafasi]:
        """Kritik durumundaki kafalları döner."""
        kafalar = self.get_all()
        return [k for k in kafalar if k.kalan_yuzdesi < 20]
