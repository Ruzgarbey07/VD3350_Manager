"""
VD3350 Manager - Ayarlar Sayfası
====================================
Kağıt türleri, makine presetleri ve uygulama ayarları.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox, QComboBox,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QTabWidget, QScrollArea,
    QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ui.widgets.common import SectionHeader, Separator
from services.preset_service import KagitTuruService, PresetService
from models import KagitTuru, MakinePreseti


class KagitTurleriTab(QWidget):
    """Kağıt türleri yönetim sekmesi."""

    liste_guncellendi = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.svc = KagitTuruService()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Ekleme formu
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(20, 16, 20, 16)
        form_layout.setSpacing(12)

        title = QLabel("➕ Yeni Kağıt Türü")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        form_layout.addWidget(title, 0, 0, 1, 4)

        def lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 12))
            return l

        form_layout.addWidget(lbl("Kağıt İsmi:"), 1, 0)
        self.isim_edit = QLineEdit()
        self.isim_edit.setPlaceholderText("ör: Kuşe, PP Opak...")
        form_layout.addWidget(self.isim_edit, 1, 1)

        form_layout.addWidget(lbl("Kalınlık (µm):"), 1, 2)
        self.kalinlik_spin = QDoubleSpinBox()
        self.kalinlik_spin.setRange(0.1, 9999.9)
        self.kalinlik_spin.setDecimals(1)
        self.kalinlik_spin.setSuffix(" µm")
        form_layout.addWidget(self.kalinlik_spin, 1, 3)

        form_layout.addWidget(lbl("Açıklama:"), 2, 0)
        self.aciklama_edit = QLineEdit()
        self.aciklama_edit.setPlaceholderText("Opsiyonel açıklama...")
        form_layout.addWidget(self.aciklama_edit, 2, 1, 1, 3)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾  Kaydet")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)
        form_layout.addLayout(btn_layout, 3, 0, 1, 4)

        layout.addWidget(form_card)

        # Liste
        list_title = QLabel("📋 Kayıtlı Kağıt Türleri")
        list_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(list_title)

        headers = ["#", "İsim", "Kalınlık (µm)", "Açıklama", "Sil"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

    def _save(self) -> None:
        """Kağıt türü kaydeder."""
        isim = self.isim_edit.text().strip()
        if not isim:
            QMessageBox.warning(self, "Uyarı", "Kağıt ismi boş bırakılamaz!")
            return

        kagit = KagitTuru(
            isim=isim,
            kalinlik_micron=self.kalinlik_spin.value(),
            aciklama=self.aciklama_edit.text().strip(),
        )
        try:
            self.svc.save(kagit)
            self.isim_edit.clear()
            self.aciklama_edit.clear()
            self.refresh()
            self.liste_guncellendi.emit()
            QMessageBox.information(self, "Başarılı", f"'{isim}' kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _delete(self, kagit_id: int, isim: str) -> None:
        """Kağıt türü siler."""
        ret = QMessageBox.question(
            self, "Silme Onayı",
            f"'{isim}' kağıt türünü silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.svc.delete(kagit_id)
            self.refresh()
            self.liste_guncellendi.emit()

    def refresh(self) -> None:
        """Tabloyu yeniler."""
        kagitlar = self.svc.get_all()
        self.table.setRowCount(len(kagitlar))
        for row, k in enumerate(kagitlar):
            cells = [
                str(row + 1),
                k.isim,
                f"{k.kalinlik_micron:.1f}",
                k.aciklama or "—",
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.table.setItem(row, col, item)

            # Sil butonu
            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("iconBtn")
            del_btn.setToolTip("Sil")
            del_btn.clicked.connect(
                lambda checked, kid=k.id, kisim=k.isim: self._delete(kid, kisim)  # type: ignore
            )
            self.table.setCellWidget(row, 4, del_btn)
            self.table.setRowHeight(row, 40)


class PresetTab(QWidget):
    """Makine presetleri yönetim sekmesi."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.svc = PresetService()
        self.kagit_svc = KagitTuruService()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Ekleme/Düzenleme formu
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QGridLayout(form_card)
        form_layout.setContentsMargins(20, 16, 20, 16)
        form_layout.setSpacing(12)

        title = QLabel("⚙️ Makine Preseti Ekle / Düzenle")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        form_layout.addWidget(title, 0, 0, 1, 6)

        def lbl(text: str) -> QLabel:
            l = QLabel(text)
            l.setFont(QFont("Segoe UI", 12))
            return l

        # Malzeme
        form_layout.addWidget(lbl("Malzeme:"), 1, 0)
        self.malzeme_combo = QComboBox()
        self.malzeme_combo.currentTextChanged.connect(self._load_preset)
        form_layout.addWidget(self.malzeme_combo, 1, 1)

        # Gramaj
        form_layout.addWidget(lbl("Gramaj (g/m²):"), 1, 2)
        self.gramaj_spin = QDoubleSpinBox()
        self.gramaj_spin.setRange(0, 9999)
        self.gramaj_spin.setDecimals(1)
        form_layout.addWidget(self.gramaj_spin, 1, 3)

        # Kalınlık
        form_layout.addWidget(lbl("Kalınlık (µm):"), 1, 4)
        self.kalinlik_spin = QDoubleSpinBox()
        self.kalinlik_spin.setRange(0, 9999)
        self.kalinlik_spin.setDecimals(1)
        form_layout.addWidget(self.kalinlik_spin, 1, 5)

        # İdeal Hız
        form_layout.addWidget(lbl("İdeal Hız (m/dk):"), 2, 0)
        self.hiz_spin = QDoubleSpinBox()
        self.hiz_spin.setRange(0, 999)
        self.hiz_spin.setDecimals(1)
        form_layout.addWidget(self.hiz_spin, 2, 1)

        # Bıçak Basıncı
        form_layout.addWidget(lbl("Bıçak Basıncı:"), 2, 2)
        self.basinc_spin = QDoubleSpinBox()
        self.basinc_spin.setRange(0, 999)
        self.basinc_spin.setDecimals(1)
        form_layout.addWidget(self.basinc_spin, 2, 3)

        # CCD
        form_layout.addWidget(lbl("CCD Hassasiyeti:"), 2, 4)
        self.ccd_spin = QDoubleSpinBox()
        self.ccd_spin.setRange(0, 99)
        self.ccd_spin.setDecimals(1)
        form_layout.addWidget(self.ccd_spin, 2, 5)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("💾  Preseti Kaydet")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._save)
        btn_layout.addWidget(self.save_btn)
        form_layout.addLayout(btn_layout, 3, 0, 1, 6)

        layout.addWidget(form_card)

        # Liste
        list_title = QLabel("📋 Kayıtlı Presetler")
        list_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(list_title)

        headers = ["Malzeme", "Gramaj", "Kalınlık (µm)", "Hız (m/dk)", "Basınç", "CCD", "İşlem"]
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)

    def _load_preset(self, malzeme: str) -> None:
        """Seçilen malzemenin presetini forma yükler."""
        preset = self.svc.get_by_malzeme(malzeme)
        if preset:
            self.gramaj_spin.setValue(preset.gramaj)
            self.kalinlik_spin.setValue(preset.kalinlik_micron)
            self.hiz_spin.setValue(preset.ideal_hiz)
            self.basinc_spin.setValue(preset.bicak_basinci)
            self.ccd_spin.setValue(preset.ccd_hassasiyeti)

    def _save(self) -> None:
        """Preseti kaydeder."""
        malzeme = self.malzeme_combo.currentText()
        if not malzeme:
            return

        preset = MakinePreseti(
            malzeme_cinsi=malzeme,
            gramaj=self.gramaj_spin.value(),
            kalinlik_micron=self.kalinlik_spin.value(),
            ideal_hiz=self.hiz_spin.value(),
            bicak_basinci=self.basinc_spin.value(),
            ccd_hassasiyeti=self.ccd_spin.value(),
        )
        try:
            self.svc.save(preset)
            self.refresh()
            QMessageBox.information(
                self, "Başarılı", f"'{malzeme}' preseti kaydedildi."
            )
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _delete(self, preset_id: int, isim: str) -> None:
        """Preseti siler."""
        ret = QMessageBox.question(
            self, "Silme Onayı",
            f"'{isim}' presetini silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.svc.delete(preset_id)
            self.refresh()

    def refresh(self) -> None:
        """Sayfayı yeniler."""
        # Malzeme listesini güncelle
        self.malzeme_combo.blockSignals(True)
        self.malzeme_combo.clear()
        names = self.kagit_svc.get_names()
        self.malzeme_combo.addItems(names)
        self.malzeme_combo.blockSignals(False)

        # Preset tablosunu güncelle
        presetler = self.svc.get_all()
        self.table.setRowCount(len(presetler))
        for row, p in enumerate(presetler):
            cells = [
                p.malzeme_cinsi,
                f"{p.gramaj:.1f}",
                f"{p.kalinlik_micron:.1f}",
                f"{p.ideal_hiz:.1f}",
                f"{p.bicak_basinci:.1f}",
                f"{p.ccd_hassasiyeti:.1f}",
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

            del_btn = QPushButton("🗑️")
            del_btn.setObjectName("iconBtn")
            del_btn.clicked.connect(
                lambda checked, pid=p.id, pisim=p.malzeme_cinsi: self._delete(pid, pisim)  # type: ignore
            )
            self.table.setCellWidget(row, 6, del_btn)
            self.table.setRowHeight(row, 40)


class AyarlarPage(QWidget):
    """Ayarlar ana sayfası."""

    kagit_listesi_guncellendi = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(16)

        header = SectionHeader("⚙️ Ayarlar", "Kağıt türleri ve makine presetlerini yönetin")
        main_layout.addWidget(header)
        main_layout.addWidget(Separator())

        # Sekmeler
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        self.kagit_tab = KagitTurleriTab()
        self.kagit_tab.liste_guncellendi.connect(self.kagit_listesi_guncellendi.emit)
        tabs.addTab(self.kagit_tab, "📄 Kağıt Türleri")

        self.preset_tab = PresetTab()
        tabs.addTab(self.preset_tab, "⚙️ Makine Presetleri")

        main_layout.addWidget(tabs)

    def refresh(self) -> None:
        """Sayfayı yeniler."""
        self.kagit_tab.refresh()
        self.preset_tab.refresh()
