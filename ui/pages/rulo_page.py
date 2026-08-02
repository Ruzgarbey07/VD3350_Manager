"""
VD3350 Manager - Rulo Hesaplama Sayfası
=========================================
Rulo çevre ölçümünden kalan metreyi hesaplar.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.widgets.common import SectionHeader, Separator
from services.preset_service import KagitTuruService, RuloService
from models import hesapla_rulo_metre


class RuloPage(QWidget):
    """Rulo çevre hesaplama sayfası."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.kagit_svc = KagitTuruService()
        self.rulo_svc = RuloService()
        self._build_ui()
        self._refresh_gecmis()

    def _build_ui(self) -> None:
        """Sayfa arayüzü."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(24)

        # Başlık
        header = SectionHeader(
            "🎯 Rulo Hesaplama",
            "Rulo çevre ölçümünden kalan metreyi hesaplayın"
        )
        main_layout.addWidget(header)
        main_layout.addWidget(Separator())

        # İki kolonlu layout
        content_row = QHBoxLayout()
        content_row.setSpacing(24)

        # Sol: Hesaplama formu
        content_row.addWidget(self._build_hesap_card(), 2)

        # Sağ: Bilgi ve geçmiş
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        right_col.addWidget(self._build_formul_card())
        right_col.addWidget(self._build_malzeme_info_card())
        right_col.addStretch()
        content_row.addLayout(right_col, 1)

        main_layout.addLayout(content_row)

        # Geçmiş
        gecmis_lbl = QLabel("📋 Hesaplama Geçmişi")
        gecmis_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        main_layout.addWidget(gecmis_lbl)
        main_layout.addWidget(self._build_gecmis_table())

    def _build_hesap_card(self) -> QFrame:
        """Hesaplama formu kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("📐 Ölçüm Girişi")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        def lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 12))
            return l

        # Malzeme seçimi
        grid.addWidget(lbl("Malzeme Türü:"), 0, 0)
        self.malzeme_combo = QComboBox()
        self.malzeme_combo.currentTextChanged.connect(self._on_malzeme_changed)
        grid.addWidget(self.malzeme_combo, 0, 1)

        # Rulonun çevresi
        grid.addWidget(lbl("Rulo Çevresi (cm):"), 1, 0)
        self.cevre_spin = QDoubleSpinBox()
        self.cevre_spin.setRange(0.1, 999.9)
        self.cevre_spin.setDecimals(1)
        self.cevre_spin.setSuffix(" cm")
        self.cevre_spin.setValue(112.0)
        self.cevre_spin.valueChanged.connect(self._on_value_changed)
        grid.addWidget(self.cevre_spin, 1, 1)

        # Kalınlık
        grid.addWidget(lbl("Malzeme Kalınlığı (µm):"), 2, 0)
        self.kalinlik_spin = QDoubleSpinBox()
        self.kalinlik_spin.setRange(0.1, 9999.9)
        self.kalinlik_spin.setDecimals(1)
        self.kalinlik_spin.setSuffix(" µm")
        self.kalinlik_spin.setValue(80.0)
        self.kalinlik_spin.valueChanged.connect(self._on_value_changed)
        grid.addWidget(self.kalinlik_spin, 2, 1)

        # İç çap
        grid.addWidget(lbl("Makara İç Çapı (cm):"), 3, 0)
        self.ic_cap_spin = QDoubleSpinBox()
        self.ic_cap_spin.setRange(1.0, 30.0)
        self.ic_cap_spin.setDecimals(1)
        self.ic_cap_spin.setSuffix(" cm")
        self.ic_cap_spin.setValue(7.6)
        self.ic_cap_spin.valueChanged.connect(self._on_value_changed)
        grid.addWidget(self.ic_cap_spin, 3, 1)

        grid.setColumnStretch(1, 2)
        layout.addLayout(grid)

        # Hesapla butonu
        self.hesapla_btn = QPushButton("🧮  Hesapla ve Kaydet")
        self.hesapla_btn.setObjectName("primaryBtn")
        self.hesapla_btn.setMinimumHeight(50)
        self.hesapla_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.hesapla_btn.clicked.connect(self._hesapla)
        layout.addWidget(self.hesapla_btn)

        # Sonuç gösterimi
        result_frame = QFrame()
        result_frame.setStyleSheet(
            "background: #1e3a5f; border-radius: 12px; border: 1px solid #3b82f6;"
        )
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(20, 16, 20, 16)

        result_title = QLabel("📏 Hesaplanan Metre:")
        result_title.setObjectName("labelMuted")
        result_title.setFont(QFont("Segoe UI", 11))
        result_layout.addWidget(result_title)

        self.sonuc_lbl = QLabel("—")
        self.sonuc_lbl.setFont(QFont("Segoe UI", 42, QFont.Weight.ExtraBold))
        self.sonuc_lbl.setStyleSheet(
            "color: #3b82f6; background: transparent; border: none;"
        )
        self.sonuc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.addWidget(self.sonuc_lbl)

        layout.addWidget(result_frame)
        self._refresh_malzeme_list()

        return card

    def _build_formul_card(self) -> QFrame:
        """Formül açıklama kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel("📐 Hesaplama Formülü")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        formul = QLabel(
            "L = π × (D_dış² − D_iç²) / (4 × t)\n\n"
            "D_dış: Dış çap (Çevre / π)\n"
            "D_iç: Makara iç çapı\n"
            "t: Malzeme kalınlığı (cm)"
        )
        formul.setObjectName("labelMuted")
        formul.setFont(QFont("Segoe UI", 11))
        formul.setWordWrap(True)
        layout.addWidget(formul)

        return card

    def _build_malzeme_info_card(self) -> QFrame:
        """Malzeme bilgi kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title = QLabel("📋 Malzeme Bilgisi")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        self.malzeme_info_lbl = QLabel("Malzeme seçin...")
        self.malzeme_info_lbl.setObjectName("labelMuted")
        self.malzeme_info_lbl.setFont(QFont("Segoe UI", 11))
        self.malzeme_info_lbl.setWordWrap(True)
        layout.addWidget(self.malzeme_info_lbl)

        return card

    def _build_gecmis_table(self) -> QTableWidget:
        """Geçmiş hesaplama tablosu."""
        headers = ["#", "Malzeme", "Çevre (cm)", "Kalınlık (µm)", "Hesaplanan (m)", "Tarih"]
        self.gecmis_table = QTableWidget()
        self.gecmis_table.setColumnCount(len(headers))
        self.gecmis_table.setHorizontalHeaderLabels(headers)
        self.gecmis_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.gecmis_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.gecmis_table.setAlternatingRowColors(True)
        self.gecmis_table.verticalHeader().setVisible(False)
        self.gecmis_table.setShowGrid(False)
        self.gecmis_table.setMaximumHeight(250)

        header = self.gecmis_table.horizontalHeader()
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        return self.gecmis_table

    def _refresh_malzeme_list(self) -> None:
        """Malzeme listesini günceller."""
        self.malzeme_combo.clear()
        kagitlar = self.kagit_svc.get_all()
        for k in kagitlar:
            self.malzeme_combo.addItem(k.isim)

    def _on_malzeme_changed(self, isim: str) -> None:
        """Malzeme seçilince kalınlığı otomatik doldurur."""
        kagit = self.kagit_svc.get_by_isim(isim)
        if kagit:
            self.kalinlik_spin.setValue(kagit.kalinlik_micron)
            self.malzeme_info_lbl.setText(
                f"İsim: {kagit.isim}\n"
                f"Kalınlık: {kagit.kalinlik_micron} µm\n"
                f"Açıklama: {kagit.aciklama or '—'}"
            )
        self._on_value_changed()

    def _on_value_changed(self) -> None:
        """Değer değişince anlık hesaplama yapar (kaydetmez)."""
        cevre = self.cevre_spin.value()
        kalinlik = self.kalinlik_spin.value()
        ic_cap = self.ic_cap_spin.value()

        if cevre > 0 and kalinlik > 0:
            sonuc = hesapla_rulo_metre(cevre, kalinlik, ic_cap)
            self.sonuc_lbl.setText(f"{sonuc:,.0f} m")
        else:
            self.sonuc_lbl.setText("—")

    def _hesapla(self) -> None:
        """Hesaplar ve geçmişe kaydeder."""
        malzeme = self.malzeme_combo.currentText()
        cevre = self.cevre_spin.value()
        kalinlik = self.kalinlik_spin.value()
        ic_cap = self.ic_cap_spin.value()

        if cevre <= 0 or kalinlik <= 0:
            return

        sonuc = self.rulo_svc.hesapla_ve_kaydet(malzeme, cevre, kalinlik, ic_cap)
        self.sonuc_lbl.setText(f"{sonuc:,.0f} m")
        self._refresh_gecmis()

    def _refresh_gecmis(self) -> None:
        """Geçmiş tablosunu günceller."""
        gecmis = self.rulo_svc.get_gecmis(30)
        self.gecmis_table.setRowCount(len(gecmis))
        for row, r in enumerate(gecmis):
            cells = [
                str(row + 1),
                r.malzeme,
                f"{r.cevre_cm:.1f}",
                f"{self.kagit_svc.get_by_isim(r.malzeme).kalinlik_micron:.1f}"
                if self.kagit_svc.get_by_isim(r.malzeme) else "—",
                f"{r.hesaplanan_metre:,.0f}",
                r.tarih[:16],
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter
                )
                if col == 4:
                    item.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                self.gecmis_table.setItem(row, col, item)
            self.gecmis_table.setRowHeight(row, 36)

    def refresh(self) -> None:
        """Sayfayı yeniler."""
        self._refresh_malzeme_list()
        self._refresh_gecmis()
