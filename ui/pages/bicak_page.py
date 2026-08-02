"""
VD3350 Manager - Bıçak Takip Sayfası
=======================================
VD3350 bıçak kafası durumu ve ömür takibi.

DÜZELTME: KafaCard'daki parentWidget().parentWidget().refresh() çağrısı
hatalıydı çünkü widget QScrollArea->QWidget->KafaGrid->KafaCard 
hiyerarşisinde olduğu için doğru parent bulunamamıyordu.
Düzeltme: refresh_callback callable parametresi kullanıldı.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QFrame, QMessageBox,
    QDoubleSpinBox, QInputDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from ui.widgets.common import SectionHeader, Separator
from services.bicak_service import BicakService
from models import BicakKafasi


class KafaCard(QFrame):
    """Tek bıçak kafası kart widget'ı."""

    def __init__(
        self,
        kafa: BicakKafasi,
        refresh_callback: Callable,
        parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.kafa = kafa
        self.svc = BicakService()
        # DÜZELTME: Doğrudan callback fonksiyon referansı kullanıyoruz
        # parent widget hiyerarşisine bağımlılık kaldırıldı
        self._refresh_callback = refresh_callback
        self.setObjectName("card")
        self.setMinimumWidth(180)
        self._build_ui()

    def _build_ui(self) -> None:
        """Kafa kartı arayüzü."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        renk = self.kafa.durum_rengi
        kalan = self.kafa.kalan_yuzdesi

        # İstasyon göstergesi
        istasyon = "İstasyon 1" if self.kafa.kafa_no <= 3 else "İstasyon 2"
        ist_lbl = QLabel(istasyon)
        ist_lbl.setObjectName("labelMuted")
        ist_lbl.setFont(QFont("Segoe UI", 9))
        ist_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ist_lbl)

        # Kafa başlığı
        title = QLabel(f"✂️ Kafa {self.kafa.kafa_no}")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.ExtraBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {renk}; background: transparent; border: none;")
        layout.addWidget(title)

        # Dairesel gösterge (metin tabanlı)
        circle_lbl = QLabel(f"{kalan:.0f}%")
        circle_lbl.setFont(QFont("Segoe UI", 32, QFont.Weight.ExtraBold))
        circle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle_lbl.setStyleSheet(
            f"color: {renk}; background: {renk}15; "
            f"border: 3px solid {renk}; border-radius: 55px; "
            f"min-width: 110px; max-width: 110px; "
            f"min-height: 110px; max-height: 110px;"
        )
        circle_layout = QHBoxLayout()
        circle_layout.addStretch()
        circle_layout.addWidget(circle_lbl)
        circle_layout.addStretch()
        layout.addLayout(circle_layout)

        # Progress bar
        pb = QProgressBar()
        pb.setRange(0, 100)
        pb.setValue(int(kalan))
        pb.setTextVisible(False)
        pb.setFixedHeight(8)
        pb.setStyleSheet(
            f"QProgressBar {{ background: #334155; border-radius: 4px; border: none; }}"
            f"QProgressBar::chunk {{ background: {renk}; border-radius: 4px; }}"
        )
        layout.addWidget(pb)

        # Kesilen metre
        metre_lbl = QLabel(f"{self.kafa.toplam_kesilen_metre:,.0f} m")
        metre_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        metre_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(metre_lbl)

        # Tahmini ömür
        omur_lbl = QLabel(f"/ {self.kafa.tahmini_omur:,.0f} m ömür")
        omur_lbl.setObjectName("labelMuted")
        omur_lbl.setFont(QFont("Segoe UI", 10))
        omur_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(omur_lbl)

        # Durum
        durum_lbl = QLabel(self.kafa.durum)
        durum_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        durum_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        durum_lbl.setStyleSheet(
            f"color: {renk}; background: {renk}22; "
            f"border: 1px solid {renk}66; border-radius: 8px; padding: 4px 12px;"
        )
        layout.addWidget(durum_lbl)

        # Tarih
        tarih_lbl = QLabel(f"📅 {self.kafa.takilan_uc_tarihi}")
        tarih_lbl.setObjectName("labelMuted")
        tarih_lbl.setFont(QFont("Segoe UI", 10))
        tarih_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tarih_lbl)

        # Uyarı
        if kalan < 20:
            uyari = QLabel("⚠️ Yakında değiştirin!")
            uyari.setStyleSheet(
                "color: #ef4444; background: #7f1d1d33; "
                "border: 1px solid #ef444466; border-radius: 6px; padding: 4px;"
            )
            uyari.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            uyari.setAlignment(Qt.AlignmentFlag.AlignCenter)
            uyari.setWordWrap(True)
            layout.addWidget(uyari)

        # Takıldı butonu
        self.takil_btn = QPushButton("🔧 Takıldı (Sıfırla)")
        self.takil_btn.setObjectName("successBtn")
        self.takil_btn.setMinimumHeight(36)
        self.takil_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.takil_btn.clicked.connect(self._takil_clicked)
        layout.addWidget(self.takil_btn)

        # Metre ekle butonu (test/ayar)
        self.metre_btn = QPushButton("+ Metre Ekle")
        self.metre_btn.setObjectName("secondaryBtn")
        self.metre_btn.setMinimumHeight(30)
        self.metre_btn.setFont(QFont("Segoe UI", 10))
        self.metre_btn.clicked.connect(self._metre_ekle)
        layout.addWidget(self.metre_btn)

    def _takil_clicked(self) -> None:
        """Yeni uç takıldı — kafayı sıfırlar."""
        ret = QMessageBox.question(
            self,
            "Uç Sıfırlama",
            f"Kafa {self.kafa.kafa_no} için yeni uç takıldı mı?\n"
            f"Bu işlem sayacı sıfırlayacak.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            try:
                self.svc.reset_kafa(self.kafa.kafa_no)
                QMessageBox.information(
                    self, "Sıfırlandı",
                    f"Kafa {self.kafa.kafa_no} sıfırlandı."
                )
                # DÜZELTME: callback ile sayfayı yenile
                self._refresh_callback()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Sıfırlama hatası: {e}")

    def _metre_ekle(self) -> None:
        """Manuel metre ekle (test/ayar amaçlı)."""
        metre, ok = QInputDialog.getDouble(
            self,
            "Metre Ekle",
            f"Kafa {self.kafa.kafa_no}'e eklenecek metre:",
            100.0, 0.1, 999999.0, 1,
        )
        if ok and metre > 0:
            try:
                self.svc.add_metre(self.kafa.kafa_no, metre)
                # DÜZELTME: callback ile sayfayı yenile
                self._refresh_callback()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Metre ekleme hatası: {e}")


class BicakTakipPage(QWidget):
    """Bıçak takip sayfası."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.svc = BicakService()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Sayfa arayüzü."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(24)

        # Başlık
        header_row = QHBoxLayout()
        header = SectionHeader(
            "🔪 Bıçak Takip Sistemi",
            "VD3350 — 6 Kafa, 2 İstasyon"
        )
        header_row.addWidget(header)
        header_row.addStretch()

        self.refresh_btn = QPushButton("🔄 Yenile")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(self.refresh_btn)

        main_layout.addLayout(header_row)
        main_layout.addWidget(Separator())

        # İstasyon bölümleri
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        # İstasyon 1 (Kafa 1-3)
        ist1_lbl = QLabel("⚙️ İstasyon 1")
        ist1_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.content_layout.addWidget(ist1_lbl)

        self.ist1_row = QHBoxLayout()
        self.ist1_row.setSpacing(16)
        self.content_layout.addLayout(self.ist1_row)

        # İstasyon 2 (Kafa 4-6)
        ist2_lbl = QLabel("⚙️ İstasyon 2")
        ist2_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.content_layout.addWidget(ist2_lbl)

        self.ist2_row = QHBoxLayout()
        self.ist2_row.setSpacing(16)
        self.content_layout.addLayout(self.ist2_row)

        # Özet istatistik
        self.content_layout.addWidget(self._build_summary_card())

        self.content_layout.addStretch()
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)

    def _build_summary_card(self) -> QFrame:
        """Özet bilgi kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(24)

        self.ozet_lbl = QLabel("Yükleniyor...")
        self.ozet_lbl.setObjectName("labelMuted")
        self.ozet_lbl.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.ozet_lbl)
        layout.addStretch()

        return card

    def _clear_layout(self, layout: QHBoxLayout) -> None:
        """Layout içindeki tüm widget'ları temizler."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self) -> None:
        """Bıçak kafalarını yeniler ve gösterir."""
        try:
            # Mevcut kartları temizle
            self._clear_layout(self.ist1_row)
            self._clear_layout(self.ist2_row)

            kafalar = self.svc.get_all()

            ist1_kafalar = [k for k in kafalar if k.kafa_no <= 3]
            ist2_kafalar = [k for k in kafalar if k.kafa_no > 3]

            # İstasyon 1 kartları
            for kafa in ist1_kafalar:
                card = KafaCard(kafa, self.refresh)  # DÜZELTME: callback geçiliyor
                self.ist1_row.addWidget(card)
            self.ist1_row.addStretch()

            # İstasyon 2 kartları
            for kafa in ist2_kafalar:
                card = KafaCard(kafa, self.refresh)  # DÜZELTME: callback geçiliyor
                self.ist2_row.addWidget(card)
            self.ist2_row.addStretch()

            # Özet güncelle
            kritik = self.svc.get_kritik_kafalar()
            if kritik:
                kafa_nos = ", ".join(str(k.kafa_no) for k in kritik)
                self.ozet_lbl.setText(
                    f"⚠️ Kritik Bıçak Kafaları: Kafa {kafa_nos} — "
                    f"Acil değişim gerekli! ({len(kritik)} adet)"
                )
                self.ozet_lbl.setStyleSheet(
                    "color: #ef4444; background: transparent; border: none;"
                )
            else:
                self.ozet_lbl.setText("✅ Tüm bıçak kafaları normal durumda.")
                self.ozet_lbl.setStyleSheet(
                    "color: #10b981; background: transparent; border: none;"
                )
        except Exception as e:
            if hasattr(self, "ozet_lbl"):
                self.ozet_lbl.setText(f"Hata: {e}")
