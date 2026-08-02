"""
VD3350 Manager - Fire Yönetimi Sayfası
=========================================
Fire ve hata kayıtlarının girişi ve görüntülenmesi.
"""

from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QDoubleSpinBox, QSpinBox, QDateEdit, QFrame, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QScrollArea
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

from ui.widgets.common import SectionHeader, Separator
from services.fire_service import FireService
from services.is_emri_service import IsEmriService
from models import FireKaydi


FIRE_NEDENLERI = [
    "Sıyırma / Waste Koptu",
    "Kamera Pozlama Kaçırdı",
    "Bıçak Kesme Hatası",
    "Malzeme Kayması",
    "Rulo Defekti",
    "Basınç Ayarı",
    "Hız Ayarı",
    "CCD Okuma Hatası",
    "Diğer",
]


class FireYonetimPage(QWidget):
    """Fire yönetimi sayfası."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.fire_svc = FireService()
        self.is_svc = IsEmriService()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Sayfa arayüzü."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(24)

        # Başlık
        header = SectionHeader(
            "🗑️ Fire Yönetimi",
            "Hata ve fire kayıtlarını yönetin"
        )
        main_layout.addWidget(header)
        main_layout.addWidget(Separator())

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Fire giriş formu
        content_layout.addWidget(self._build_form_card())

        # Özet istatistikler
        content_layout.addWidget(self._build_stats_card())

        # Fire listesi
        content_layout.addWidget(QLabel("📋 Fire Kayıtları"))
        content_layout.addWidget(self._build_table())

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _build_form_card(self) -> QFrame:
        """Fire giriş formu kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("➕ Yeni Fire Kaydı")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        def lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 12))
            return l

        # Form No
        grid.addWidget(lbl("Form Numarası"), 0, 0)
        self.form_no_combo = QComboBox()
        self.form_no_combo.setEditable(True)
        self.form_no_combo.lineEdit().setPlaceholderText("Form no seçin veya girin...")  # type: ignore
        grid.addWidget(self.form_no_combo, 0, 1)

        # Tarih
        grid.addWidget(lbl("Tarih"), 0, 2)
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.setDisplayFormat("dd.MM.yyyy")
        grid.addWidget(self.tarih_edit, 0, 3)

        # Hatalı Metre
        grid.addWidget(lbl("Hatalı Metre"), 1, 0)
        self.metre_spin = QDoubleSpinBox()
        self.metre_spin.setRange(0, 99999)
        self.metre_spin.setDecimals(2)
        self.metre_spin.setSuffix(" m")
        self.metre_spin.setSpecialValueText("— (metre yok)")
        grid.addWidget(self.metre_spin, 1, 1)

        # Hatalı Adet
        grid.addWidget(lbl("Hatalı Adet"), 1, 2)
        self.adet_spin = QSpinBox()
        self.adet_spin.setRange(0, 9999999)
        self.adet_spin.setSuffix(" adet")
        self.adet_spin.setSpecialValueText("— (adet yok)")
        grid.addWidget(self.adet_spin, 1, 3)

        # Fire Nedeni
        grid.addWidget(lbl("Fire Nedeni"), 2, 0)
        self.neden_combo = QComboBox()
        self.neden_combo.addItems(FIRE_NEDENLERI)
        grid.addWidget(self.neden_combo, 2, 1)

        # Açıklama
        grid.addWidget(lbl("Açıklama"), 2, 2)
        self.aciklama_edit = QLineEdit()
        self.aciklama_edit.setPlaceholderText("Ek not...")
        grid.addWidget(self.aciklama_edit, 2, 3)

        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)
        layout.addLayout(grid)

        # Bilgi notu
        info = QLabel(
            "ℹ️  Hatalı Metre ve Hatalı Adet alanları bağımsızdır. "
            "Sadece metre, sadece adet veya ikisi birlikte girilebilir. Boş bırakılabilir."
        )
        info.setObjectName("labelMuted")
        info.setFont(QFont("Segoe UI", 11))
        info.setWordWrap(True)
        layout.addWidget(info)

        # Kaydet butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾  Fire Kaydını Kaydet")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setMinimumWidth(200)
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        return card

    def _build_stats_card(self) -> QFrame:
        """Özet istatistik kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(32)

        def stat(icon: str, label: str, color: str) -> QLabel:
            lbl = QLabel(f"{icon}  {label}")
            lbl.setFont(QFont("Segoe UI", 13))
            lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
            return lbl

        self.toplam_fire_lbl = stat("🗑️", "Toplam Fire: 0 m", "#ef4444")
        self.kayit_sayisi_lbl = stat("📋", "Toplam Kayıt: 0", "#3b82f6")
        self.en_cok_neden_lbl = stat("📌", "En Çok: —", "#f59e0b")

        layout.addWidget(self.toplam_fire_lbl)
        layout.addWidget(self.kayit_sayisi_lbl)
        layout.addWidget(self.en_cok_neden_lbl)
        layout.addStretch()

        return card

    def _build_table(self) -> QTableWidget:
        """Fire kayıtları tablosu."""
        headers = ["#", "Form No", "Tarih", "Hatalı Metre", "Hatalı Adet", "Neden", "Açıklama"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(300)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        return self.table

    def _populate_table(self, kayitlar: list[FireKaydi]) -> None:
        """Tabloyu doldurur."""
        self.table.setRowCount(len(kayitlar))
        for row, k in enumerate(kayitlar):
            cells = [
                str(row + 1),
                k.form_numarasi or "—",
                k.tarih,
                f"{k.hatali_metre:.2f} m" if k.hatali_metre else "—",
                f"{k.hatali_adet:,}" if k.hatali_adet else "—",
                k.fire_nedeni or "—",
                k.aciklama or "—",
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                if col == 3 and k.hatali_metre:
                    item.setForeground(QColor("#ef4444"))
                self.table.setItem(row, col, item)
            self.table.setRowHeight(row, 40)

    def _update_stats(self) -> None:
        """İstatistikleri günceller."""
        kayitlar = self.fire_svc.get_all()
        toplam_fire = sum(k.hatali_metre or 0 for k in kayitlar)
        self.toplam_fire_lbl.setText(f"🗑️  Toplam Fire: {toplam_fire:,.2f} m")
        self.kayit_sayisi_lbl.setText(f"📋  Toplam Kayıt: {len(kayitlar)}")

        nedenler = self.fire_svc.get_fire_nedenleri()
        if nedenler:
            en_cok = nedenler[0]["fire_nedeni"]
            self.en_cok_neden_lbl.setText(f"📌  En Çok: {en_cok}")

    def _refresh_form_no_list(self) -> None:
        """Form no listesini günceller."""
        self.form_no_combo.clear()
        self.form_no_combo.addItem("")
        emirler = self.is_svc.get_all()
        for e in emirler:
            self.form_no_combo.addItem(e.form_numarasi)

    def _save(self) -> None:
        """Fire kaydını kaydeder."""
        hatali_metre = self.metre_spin.value() if self.metre_spin.value() > 0 else None
        hatali_adet = self.adet_spin.value() if self.adet_spin.value() > 0 else None

        if hatali_metre is None and hatali_adet is None:
            QMessageBox.warning(
                self, "Uyarı",
                "En az 'Hatalı Metre' veya 'Hatalı Adet' girilmelidir."
            )
            return

        form_no = self.form_no_combo.currentText().strip() or None
        tarih = self.tarih_edit.date().toString("yyyy-MM-dd")

        kayit = FireKaydi(
            form_numarasi=form_no,
            tarih=tarih,
            hatali_metre=hatali_metre,
            hatali_adet=hatali_adet,
            fire_nedeni=self.neden_combo.currentText(),
            aciklama=self.aciklama_edit.text().strip(),
        )

        try:
            self.fire_svc.create(kayit)
            QMessageBox.information(self, "Başarılı", "Fire kaydı oluşturuldu.")
            self._clear_form()
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")

    def _clear_form(self) -> None:
        """Formu temizler."""
        self.form_no_combo.setCurrentIndex(0)
        self.tarih_edit.setDate(QDate.currentDate())
        self.metre_spin.setValue(0)
        self.adet_spin.setValue(0)
        self.aciklama_edit.clear()

    def refresh(self) -> None:
        """Sayfayı yeniler."""
        self._refresh_form_no_list()
        kayitlar = self.fire_svc.get_all()
        self._populate_table(kayitlar)
        self._update_stats()
