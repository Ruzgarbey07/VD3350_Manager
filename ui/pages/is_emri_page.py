"""
VD3350 Manager - İş Emri Sayfası
=====================================
Yeni iş emri girişi formu.
"""

from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QDoubleSpinBox, QSpinBox, QDateEdit, QFrame, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont

from ui.widgets.common import SectionHeader, Separator
from services.is_emri_service import IsEmriService
from services.preset_service import KagitTuruService, PresetService
from models import IsEmri


class IsEmriForm(QWidget):
    """
    Yeni iş emri formu.
    Kaydetme sonrası iş kuyruğuna otomatik eklenir.
    """

    is_kaydedildi = pyqtSignal()  # İş kaydedilince sinyal

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.is_emri_svc = IsEmriService()
        self.kagit_svc = KagitTuruService()
        self.preset_svc = PresetService()
        self._build_ui()

    def _build_ui(self) -> None:
        """Form arayüzünü oluşturur."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(24)

        # Başlık
        header = SectionHeader(
            "➕ Yeni İş Emri",
            "Kesim işlemi için iş emri oluşturun"
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

        # Form kartı
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QGridLayout(form_card)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(24, 24, 24, 24)

        # Form alanlarını oluştur
        self._build_form_fields(form_layout)
        content_layout.addWidget(form_card)

        # Preset bilgi kartı
        self.preset_card = self._build_preset_card()
        content_layout.addWidget(self.preset_card)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.clear_btn = QPushButton("🗑️  Formu Temizle")
        self.clear_btn.setObjectName("secondaryBtn")
        self.clear_btn.clicked.connect(self._clear_form)

        self.save_btn = QPushButton("💾  İş Emri Kaydet")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setMinimumWidth(180)
        self.save_btn.clicked.connect(self._save)

        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.save_btn)
        content_layout.addLayout(btn_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _build_form_fields(self, layout: QGridLayout) -> None:
        """Form alanlarını grid'e yerleştirir."""

        def label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 12))
            return lbl

        # Form No
        layout.addWidget(label("Form Numarası *"), 0, 0)
        self.form_no_edit = QLineEdit()
        self.form_no_edit.setPlaceholderText("Otomatik oluşturulacak...")
        self.form_no_edit.setText(self.is_emri_svc.generate_form_no())
        layout.addWidget(self.form_no_edit, 0, 1)

        # Tarih
        layout.addWidget(label("Tarih *"), 0, 2)
        self.tarih_edit = QDateEdit()
        self.tarih_edit.setDate(QDate.currentDate())
        self.tarih_edit.setCalendarPopup(True)
        self.tarih_edit.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(self.tarih_edit, 0, 3)

        # Müşteri
        layout.addWidget(label("Müşteri Adı *"), 1, 0)
        self.musteri_edit = QLineEdit()
        self.musteri_edit.setPlaceholderText("Müşteri adı girin...")
        layout.addWidget(self.musteri_edit, 1, 1, 1, 3)

        # Malzeme Cinsi
        layout.addWidget(label("Malzeme Cinsi *"), 2, 0)
        self.malzeme_combo = QComboBox()
        self._refresh_malzeme_list()
        self.malzeme_combo.currentTextChanged.connect(self._on_malzeme_changed)
        layout.addWidget(self.malzeme_combo, 2, 1)

        # Etiket Ölçüleri
        layout.addWidget(label("Etiket Genişliği (mm) *"), 2, 2)
        self.genislik_spin = QDoubleSpinBox()
        self.genislik_spin.setRange(1, 9999)
        self.genislik_spin.setDecimals(1)
        self.genislik_spin.setSuffix(" mm")
        layout.addWidget(self.genislik_spin, 2, 3)

        layout.addWidget(label("Etiket Yüksekliği (mm) *"), 3, 0)
        self.yukseklik_spin = QDoubleSpinBox()
        self.yukseklik_spin.setRange(1, 9999)
        self.yukseklik_spin.setDecimals(1)
        self.yukseklik_spin.setSuffix(" mm")
        layout.addWidget(self.yukseklik_spin, 3, 1)

        # Metraj
        layout.addWidget(label("Metraj (m) *"), 3, 2)
        self.metraj_spin = QDoubleSpinBox()
        self.metraj_spin.setRange(0.1, 999999)
        self.metraj_spin.setDecimals(1)
        self.metraj_spin.setSuffix(" m")
        layout.addWidget(self.metraj_spin, 3, 3)

        # Adet
        layout.addWidget(label("Adet *"), 4, 0)
        self.adet_spin = QSpinBox()
        self.adet_spin.setRange(1, 9999999)
        self.adet_spin.setSuffix(" adet")
        layout.addWidget(self.adet_spin, 4, 1)

        # Açıklama
        layout.addWidget(label("Açıklama"), 4, 2)
        self.aciklama_edit = QTextEdit()
        self.aciklama_edit.setMaximumHeight(80)
        self.aciklama_edit.setPlaceholderText("Ek notlar...")
        layout.addWidget(self.aciklama_edit, 4, 3)

        # Sütun genişlikleri
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 2)

    def _build_preset_card(self) -> QFrame:
        """Makine preset bilgi kartı."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)

        title = QLabel("⚙️ Seçilen Malzeme İçin Makine Ayarları")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        self.preset_info_layout = QHBoxLayout()
        self.preset_info_layout.setSpacing(32)

        self.hiz_lbl = self._preset_label("Hız", "—", "m/dk", "#3b82f6")
        self.basinc_lbl = self._preset_label("Bıçak Basıncı", "—", "", "#10b981")
        self.ccd_lbl = self._preset_label("CCD Hassasiyeti", "—", "", "#f59e0b")
        self.kalinlik_lbl = self._preset_label("Kalınlık", "—", "µm", "#8b5cf6")

        for w in [self.hiz_lbl, self.basinc_lbl, self.ccd_lbl, self.kalinlik_lbl]:
            self.preset_info_layout.addWidget(w)
        self.preset_info_layout.addStretch()

        layout.addLayout(self.preset_info_layout)
        return card

    def _preset_label(
        self, title: str, value: str, unit: str, color: str
    ) -> QFrame:
        """Tek preset bilgi widget'ı."""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        t = QLabel(title)
        t.setObjectName("labelMuted")
        t.setFont(QFont("Segoe UI", 10))
        layout.addWidget(t)

        val_layout = QHBoxLayout()
        v = QLabel(value)
        v.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        v.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        frame._value_lbl = v  # type: ignore
        frame._unit = unit  # type: ignore
        val_layout.addWidget(v)

        if unit:
            u = QLabel(unit)
            u.setObjectName("labelMuted")
            u.setFont(QFont("Segoe UI", 10))
            u.setAlignment(Qt.AlignmentFlag.AlignBottom)
            val_layout.addWidget(u)

        val_layout.addStretch()
        layout.addLayout(val_layout)
        return frame

    def _on_malzeme_changed(self, malzeme: str) -> None:
        """Malzeme seçilince preset bilgilerini günceller."""
        preset = self.preset_svc.get_by_malzeme(malzeme)
        if preset:
            self.hiz_lbl._value_lbl.setText(str(preset.ideal_hiz))  # type: ignore
            self.basinc_lbl._value_lbl.setText(str(preset.bicak_basinci))  # type: ignore
            self.ccd_lbl._value_lbl.setText(str(preset.ccd_hassasiyeti))  # type: ignore
            self.kalinlik_lbl._value_lbl.setText(str(preset.kalinlik_micron))  # type: ignore
        else:
            for lbl in [self.hiz_lbl, self.basinc_lbl, self.ccd_lbl, self.kalinlik_lbl]:
                lbl._value_lbl.setText("—")  # type: ignore

    def _refresh_malzeme_list(self) -> None:
        """Malzeme listesini veritabanından günceller."""
        self.malzeme_combo.clear()
        names = self.kagit_svc.get_names()
        self.malzeme_combo.addItems(names if names else ["Kuşe", "PP Opak", "Termal"])

    def _validate(self) -> bool:
        """Form doğrulaması yapar."""
        if not self.form_no_edit.text().strip():
            self._show_error("Form numarası boş bırakılamaz!")
            return False
        if not self.musteri_edit.text().strip():
            self._show_error("Müşteri adı boş bırakılamaz!")
            return False
        if self.metraj_spin.value() <= 0:
            self._show_error("Metraj 0'dan büyük olmalıdır!")
            return False
        if self.adet_spin.value() <= 0:
            self._show_error("Adet 0'dan büyük olmalıdır!")
            return False
        return True

    def _show_error(self, message: str) -> None:
        """Hata mesajı gösterir."""
        QMessageBox.warning(self, "Doğrulama Hatası", message)

    def _save(self) -> None:
        """İş emrini kaydeder."""
        if not self._validate():
            return

        tarih = self.tarih_edit.date().toString("yyyy-MM-dd")
        emri = IsEmri(
            form_numarasi=self.form_no_edit.text().strip(),
            tarih=tarih,
            musteri_adi=self.musteri_edit.text().strip(),
            malzeme_cinsi=self.malzeme_combo.currentText(),
            etiket_genisligi=self.genislik_spin.value(),
            etiket_yuksekligi=self.yukseklik_spin.value(),
            metraj=self.metraj_spin.value(),
            adet=self.adet_spin.value(),
            durum="Bekliyor",
            aciklama=self.aciklama_edit.toPlainText().strip(),
        )

        try:
            self.is_emri_svc.create(emri)
            QMessageBox.information(
                self,
                "Başarılı",
                f"İş emri '{emri.form_numarasi}' kaydedildi ve kuyruğa eklendi.",
            )
            self.is_kaydedildi.emit()
            self._clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kayıt hatası: {e}")

    def _clear_form(self) -> None:
        """Formu temizler."""
        self.form_no_edit.setText(self.is_emri_svc.generate_form_no())
        self.tarih_edit.setDate(QDate.currentDate())
        self.musteri_edit.clear()
        self.metraj_spin.setValue(0)
        self.adet_spin.setValue(1)
        self.genislik_spin.setValue(0)
        self.yukseklik_spin.setValue(0)
        self.aciklama_edit.clear()

    def refresh(self) -> None:
        """Malzeme listesini yeniler."""
        self._refresh_malzeme_list()
