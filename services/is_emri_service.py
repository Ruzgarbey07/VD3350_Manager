"""
VD3350 Manager - İş Emri Servisi
===================================
İş emirleri ile ilgili tüm iş mantığı bu modülde yer alır.
"""

from datetime import datetime
from typing import Optional
from database import db
from models import IsEmri


class IsEmriService:
    """İş emri CRUD ve iş mantığı işlemleri."""

    def create(self, emri: IsEmri) -> int:
        """Yeni iş emri oluşturur ve ID'sini döner."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = db.execute(
            """INSERT INTO is_emirleri
               (form_numarasi, tarih, musteri_adi, malzeme_cinsi,
                etiket_genisligi, etiket_yuksekligi, metraj, adet,
                durum, aciklama, olusturulma_tarihi, guncellenme_tarihi)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                emri.form_numarasi,
                emri.tarih,
                emri.musteri_adi,
                emri.malzeme_cinsi,
                emri.etiket_genisligi,
                emri.etiket_yuksekligi,
                emri.metraj,
                emri.adet,
                emri.durum,
                emri.aciklama,
                now,
                now,
            ),
        )
        return cursor.lastrowid  # type: ignore

    def get_all(self, durum_filtre: Optional[str] = None) -> list[IsEmri]:
        """Tüm iş emirlerini listeler, opsiyonel durum filtresi."""
        if durum_filtre and durum_filtre != "Tümü":
            rows = db.fetchall(
                "SELECT * FROM is_emirleri WHERE durum = ? ORDER BY olusturulma_tarihi DESC",
                (durum_filtre,),
            )
        else:
            rows = db.fetchall(
                "SELECT * FROM is_emirleri ORDER BY olusturulma_tarihi DESC"
            )
        return [IsEmri.from_row(r) for r in rows]

    def get_by_id(self, emri_id: int) -> Optional[IsEmri]:
        """ID'ye göre iş emri getirir."""
        row = db.fetchone("SELECT * FROM is_emirleri WHERE id = ?", (emri_id,))
        return IsEmri.from_row(row) if row else None

    def get_by_form_no(self, form_no: str) -> Optional[IsEmri]:
        """Form numarasına göre iş emri getirir."""
        row = db.fetchone(
            "SELECT * FROM is_emirleri WHERE form_numarasi = ?", (form_no,)
        )
        return IsEmri.from_row(row) if row else None

    def update_durum(self, emri_id: int, yeni_durum: str) -> None:
        """İş emrinin durumunu günceller."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "UPDATE is_emirleri SET durum = ?, guncellenme_tarihi = ? WHERE id = ?",
            (yeni_durum, now, emri_id),
        )

    def update(self, emri: IsEmri) -> None:
        """İş emrini günceller."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            """UPDATE is_emirleri SET
               form_numarasi = ?, tarih = ?, musteri_adi = ?,
               malzeme_cinsi = ?, etiket_genisligi = ?, etiket_yuksekligi = ?,
               metraj = ?, adet = ?, durum = ?, aciklama = ?,
               guncellenme_tarihi = ?
               WHERE id = ?""",
            (
                emri.form_numarasi,
                emri.tarih,
                emri.musteri_adi,
                emri.malzeme_cinsi,
                emri.etiket_genisligi,
                emri.etiket_yuksekligi,
                emri.metraj,
                emri.adet,
                emri.durum,
                emri.aciklama,
                now,
                emri.id,
            ),
        )

    def delete(self, emri_id: int) -> None:
        """İş emrini siler."""
        db.execute("DELETE FROM is_emirleri WHERE id = ?", (emri_id,))

    def search(self, query: str) -> list[IsEmri]:
        """Form no, müşteri veya malzemeye göre arama yapar."""
        like = f"%{query}%"
        rows = db.fetchall(
            """SELECT * FROM is_emirleri
               WHERE form_numarasi LIKE ? OR musteri_adi LIKE ? OR malzeme_cinsi LIKE ?
               ORDER BY olusturulma_tarihi DESC""",
            (like, like, like),
        )
        return [IsEmri.from_row(r) for r in rows]

    def get_bugunun_emirleri(self) -> list[IsEmri]:
        """Bugünün iş emirlerini getirir."""
        bugun = datetime.now().strftime("%Y-%m-%d")
        rows = db.fetchall(
            "SELECT * FROM is_emirleri WHERE tarih = ? ORDER BY olusturulma_tarihi DESC",
            (bugun,),
        )
        return [IsEmri.from_row(r) for r in rows]

    def get_dashboard_stats(self) -> dict:
        """Dashboard için özet istatistikler döner."""
        bugun = datetime.now().strftime("%Y-%m-%d")

        # Bugünkü tamamlanan iş sayısı
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM is_emirleri WHERE tarih = ? AND durum = 'Tamamlandı'",
            (bugun,),
        )
        gunluk_is = row["cnt"] if row else 0

        # Bugünkü toplam metraj
        row = db.fetchone(
            """SELECT COALESCE(SUM(metraj), 0) as toplam
               FROM is_emirleri WHERE tarih = ? AND durum = 'Tamamlandı'""",
            (bugun,),
        )
        gunluk_metraj = row["toplam"] if row else 0.0

        # Toplam fire miktarı (bugün)
        row = db.fetchone(
            """SELECT COALESCE(SUM(hatali_metre), 0) as toplam
               FROM fire_ve_hatalar WHERE tarih = ?""",
            (bugun,),
        )
        gunluk_fire = row["toplam"] if row else 0.0

        # Fire oranı
        fire_orani = 0.0
        if gunluk_metraj > 0:
            fire_orani = (gunluk_fire / gunluk_metraj) * 100

        # Ortalama günlük üretim (son 30 gün)
        row = db.fetchone(
            """SELECT COALESCE(AVG(gunluk_metraj), 0) as ort FROM (
                SELECT tarih, SUM(metraj) as gunluk_metraj
                FROM is_emirleri
                WHERE durum = 'Tamamlandı'
                  AND tarih >= date('now', '-30 days')
                GROUP BY tarih
            )"""
        )
        ort_uretim = row["ort"] if row else 0.0

        # Bugünkü hatalı kesim sayısı
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM is_emirleri WHERE tarih = ? AND durum = 'Hatalı Kesim'",
            (bugun,),
        )
        hatali_kesim = row["cnt"] if row else 0

        return {
            "gunluk_is": gunluk_is,
            "gunluk_metraj": gunluk_metraj,
            "gunluk_fire": gunluk_fire,
            "fire_orani": fire_orani,
            "ort_uretim": ort_uretim,
            "hatali_kesim": hatali_kesim,
        }

    def get_son_30_gun_uretim(self) -> list[dict]:
        """Son 30 günün günlük üretim verilerini döner."""
        rows = db.fetchall(
            """SELECT tarih, SUM(metraj) as toplam_metraj, COUNT(*) as is_sayisi
               FROM is_emirleri
               WHERE durum = 'Tamamlandı'
                 AND tarih >= date('now', '-30 days')
               GROUP BY tarih
               ORDER BY tarih"""
        )
        return [dict(r) for r in rows]

    def get_malzeme_kullanim(self) -> list[dict]:
        """Malzeme kullanım dağılımını döner."""
        rows = db.fetchall(
            """SELECT malzeme_cinsi, SUM(metraj) as toplam_metraj, COUNT(*) as is_sayisi
               FROM is_emirleri
               WHERE durum = 'Tamamlandı'
               GROUP BY malzeme_cinsi
               ORDER BY toplam_metraj DESC
               LIMIT 8"""
        )
        return [dict(r) for r in rows]

    def generate_form_no(self) -> str:
        """Otomatik form numarası üretir."""
        tarih = datetime.now().strftime("%Y%m%d")
        row = db.fetchone(
            "SELECT COUNT(*) as cnt FROM is_emirleri WHERE form_numarasi LIKE ?",
            (f"IE{tarih}%",),
        )
        sira = (row["cnt"] if row else 0) + 1
        return f"IE{tarih}{sira:03d}"
