"""
VD3350 Manager - Hızlı Operatör Paneli
=========================================
Operatörün tek tıkla iş sonuçlandırması için büyük buton paneli.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QMessageBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ui.widgets.common import SectionHeader, Separator
from services.is_emri_service import IsEmriService
from services.fire_service import FireService
from services.bicak_service import BicakService


class OperatorPanel(QWidget):
    """
    Hızlı operatör paneli.
    3 büyük buton: Temiz Bitti / Sıyırma Koptu / Kamera Hatası
    """

    is_guncellendi = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.is_svc = IsEmriService()
        self.fire_svc = FireService()
        self.bicak_svc = BicakService()

        # Sayaç değişkenleri
        self._kalan_metre: float = 0.0
        self._makine_hizi: float = 0.0
        self._sayac_timer = QTimer(self)
        self._sayac_timer.timeout.connect(self._sayac_tick)
        self._gecen_saniye: int = 0

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Panel arayüzü."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(24)

        # Başlık
        header = SectionHeader(
            "🎮 Operatör Paneli",
            "Hızlı iş bitiş ve fire kayıt ekranı"
        )
        main_layout.addWidget(header)
        main_layout.addWidget(Separator())

        # İş seçim kartı
        is_card = self._build_is_secim_card()
        main_layout.addWidget(is_card)

        # Büyük buton satırı
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.temiz_btn = self._make_big_btn(
            "✅  Temiz Bitti",
            "İşi tamamlandı olarak işaretler.\nMetrajı üretime ekler.",
            "#successBtn",
            self._temiz_bitti,
        )
        self.siyirma_btn = self._make_big_btn(
            "⚠️  Sıyırma / Waste Koptu",
            "+2 metre fire ekler.\nİş tamamlandı olarak işaretlenir.",
            "#warningBtn",
            self._siyirma_koptu,
        )
        self.kamera_btn = self._make_big_btn(
            "❌  Kamera Pozlama Kaçırdı",
            "İş 'Hatalı Kesim' olarak işaretlenir.\nFire kaydına eklenir.",
            "#dangerBtn",
            self._kamera_hatasi,
        )

        btn_row.addWidget(self.temiz_btn, 1)
        btn_row.addWidget(self.siyirma_btn, 1)
        btn_row.addWidget(self.kamera_btn, 1)
        main_layout.addLayout(btn_row)

        # İş bitiş sayacı
        sayac_card = self._build_sayac_card()
        main_layout.addWidget(sayac_card)

        main_layout.addStretch()

    def _build_is_secim_card(self) -> QFrame:
        """İş seçim kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        icon = QLabel("📋")
        icon.setFont(QFont("Segoe UI Emoji", 24))
        layout.addWidget(icon)

        lbl = QLabel("Aktif İş Emri:")
        lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.is_combo = QComboBox()
        self.is_combo.setMinimumWidth(320)
        self.is_combo.setFont(QFont("Segoe UI", 12))
        self.is_combo.currentTextChanged.connect(self._on_is_changed)
        layout.addWidget(self.is_combo)

        layout.addStretch()

        # Aktif iş bilgisi
        self.is_bilgi_lbl = QLabel("—")
        self.is_bilgi_lbl.setObjectName("labelMuted")
        self.is_bilgi_lbl.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.is_bilgi_lbl)

        return card

    def _make_big_btn(
        self, text: str, tooltip: str, style_id: str, callback
    ) -> QPushButton:
        """Büyük aksiyon butonu oluşturur."""
        btn = QPushButton(text)
        btn.setObjectName(style_id.replace("#", ""))
        btn.setMinimumHeight(100)
        btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        return btn

    def _build_sayac_card(self) -> QFrame:
        """İş bitiş sayacı kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("⏱️ İş Bitiş Sayacı")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.setSpacing(16)

        # Makine hızı
        hiz_lbl = QLabel("Makine Hızı:")
        hiz_lbl.setFont(QFont("Segoe UI", 12))
        controls.addWidget(hiz_lbl)

        self.hiz_spin = QDoubleSpinBox()
        self.hiz_spin.setRange(0.1, 100)
        self.hiz_spin.setDecimals(1)
        self.hiz_spin.setValue(10.0)
        self.hiz_spin.setSuffix(" m/dk")
        controls.addWidget(self.hiz_spin)

        # Kalan metraj
        kalan_lbl = QLabel("Kalan Metraj:")
        kalan_lbl.setFont(QFont("Segoe UI", 12))
        controls.addWidget(kalan_lbl)

        self.kalan_spin = QDoubleSpinBox()
        self.kalan_spin.setRange(0, 999999)
        self.kalan_spin.setDecimals(1)
        self.kalan_spin.setValue(0)
        self.kalan_spin.setSuffix(" m")
        controls.addWidget(self.kalan_spin)

        # Başlat/Durdur
        self.sayac_btn = QPushButton("▶ Sayacı Başlat")
        self.sayac_btn.setObjectName("primaryBtn")
        self.sayac_btn.clicked.connect(self._toggle_sayac)
        controls.addWidget(self.sayac_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Kalan süre gösterimi
        self.kalan_sure_lbl = QLabel("⏰ Kalan Süre: —")
        self.kalan_sure_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.ExtraBold))
        self.kalan_sure_lbl.setStyleSheet(
            "color: #3b82f6; background: transparent; border: none;"
        )
        self.kalan_sure_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.kalan_sure_lbl)

        return card

    def _on_is_changed(self, text: str) -> None:
        """İş seçilince bilgileri gösterir."""
        form_no = text.split(" — ")[0] if " — " in text else text
        emri = self.is_svc.get_by_form_no(form_no)
        if emri:
            self.is_bilgi_lbl.setText(
                f"{emri.musteri_adi} | {emri.malzeme_cinsi} | {emri.metraj:.0f} m"
            )
            self.kalan_spin.setValue(emri.metraj)
        else:
            self.is_bilgi_lbl.setText("—")

    def _get_secili_emri(self):  # type: ignore
        """Seçili iş emrini döner."""
        text = self.is_combo.currentText()
        if not text or text == "— İş seçin —":
            return None
        form_no = text.split(" — ")[0]
        return self.is_svc.get_by_form_no(form_no)

    def _temiz_bitti(self) -> None:
        """İşi tamamlandı olarak işaretler."""
        emri = self._get_secili_emri()
        if not emri:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir iş emri seçin.")
            return

        self.is_svc.update_durum(emri.id, "Tamamlandı")  # type: ignore

        # Bıçak kafalarına metre ekle
        self.bicak_svc.add_all_kafalar(emri.metraj)

        self.is_guncellendi.emit()
        self.refresh()

        msg = QMessageBox(self)
        msg.setWindowTitle("✅ Tamamlandı")
        msg.setText(
            f"<b>{emri.form_numarasi}</b> iş emri tamamlandı olarak işaretlendi.\n"
            f"{emri.metraj:.0f} m üretim kaydedildi."
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def _siyirma_koptu(self) -> None:
        """Sıyırma/waste fire ekler ve işi tamamlar."""
        emri = self._get_secili_emri()
        if not emri:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir iş emri seçin.")
            return

        # +2 metre fire ekle
        self.fire_svc.add_waste_fire(emri.form_numarasi, 2.0)

        # İşi tamamlandı yap
        self.is_svc.update_durum(emri.id, "Tamamlandı")  # type: ignore

        # Bıçak kafalarına metre ekle
        self.bicak_svc.add_all_kafalar(emri.metraj)

        self.is_guncellendi.emit()
        self.refresh()

        msg = QMessageBox(self)
        msg.setWindowTitle("⚠️ Sıyırma Kaydedildi")
        msg.setText(
            f"<b>{emri.form_numarasi}</b> için +2 metre fire eklendi.\n"
            f"İş tamamlandı olarak işaretlendi."
        )
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.exec()

    def _kamera_hatasi(self) -> None:
        """Kamera hatası — iş hatalı kesim olarak işaretlenir."""
        emri = self._get_secili_emri()
        if not emri:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir iş emri seçin.")
            return

        self.fire_svc.add_kamera_fire(emri.form_numarasi)
        self.is_svc.update_durum(emri.id, "Hatalı Kesim")  # type: ignore

        self.is_guncellendi.emit()
        self.refresh()

        msg = QMessageBox(self)
        msg.setWindowTitle("❌ Hatalı Kesim")
        msg.setText(
            f"<b>{emri.form_numarasi}</b> 'Hatalı Kesim' olarak işaretlendi.\n"
            f"Fire kaydına eklendi."
        )
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.exec()

    def _toggle_sayac(self) -> None:
        """Sayacı başlatır veya durdurur."""
        if self._sayac_timer.isActive():
            self._sayac_timer.stop()
            self.sayac_btn.setText("▶ Sayacı Başlat")
        else:
            self._makine_hizi = self.hiz_spin.value()
            self._kalan_metre = self.kalan_spin.value()
            self._gecen_saniye = 0
            if self._makine_hizi <= 0 or self._kalan_metre <= 0:
                QMessageBox.warning(
                    self, "Uyarı", "Hız ve kalan metraj 0'dan büyük olmalıdır."
                )
                return
            self._sayac_timer.start(1000)  # Her saniye
            self.sayac_btn.setText("⏹ Sayacı Durdur")
            self.sayac_btn.setObjectName("dangerBtn")

    def _sayac_tick(self) -> None:
        """Her saniyede bir sayacı günceller."""
        self._gecen_saniye += 1
        gecen_metre = (self._makine_hizi / 60) * self._gecen_saniye
        kalan = self._kalan_metre - gecen_metre

        if kalan <= 0:
            self._sayac_timer.stop()
            self.kalan_sure_lbl.setText("✅ İş Tamamlandı!")
            self.sayac_btn.setText("▶ Sayacı Başlat")
            self.sayac_btn.setObjectName("primaryBtn")
            return

        # Kalan süre (saniye)
        kalan_saniye = int((kalan / self._makine_hizi) * 60)
        dakika = kalan_saniye // 60
        saniye = kalan_saniye % 60
        self.kalan_sure_lbl.setText(
            f"⏰ Kalan: {dakika:02d}:{saniye:02d} — {kalan:.0f} m"
        )

    def refresh(self) -> None:
        """Bekleyen iş emirlerini günceller."""
        self.is_combo.blockSignals(True)
        current = self.is_combo.currentText()
        self.is_combo.clear()
        self.is_combo.addItem("— İş seçin —")

        emirler = self.is_svc.get_all()
        bekleyen = [e for e in emirler if e.durum in ("Bekliyor", "Devam Ediyor")]

        for emri in bekleyen:
            self.is_combo.addItem(
                f"{emri.form_numarasi} — {emri.musteri_adi} ({emri.metraj:.0f} m)"
            )

        # Önceki seçimi koru
        idx = self.is_combo.findText(current)
        if idx >= 0:
            self.is_combo.setCurrentIndex(idx)

        self.is_combo.blockSignals(False)
