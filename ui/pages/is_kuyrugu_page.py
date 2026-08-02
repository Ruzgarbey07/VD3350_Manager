"""
VD3350 Manager - İş Kuyruğu Sayfası
======================================
İş emirlerini listeler, filtreler ve durum yönetimi sağlar.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QFrame,
    QDialog, QGridLayout, QTextEdit, QDoubleSpinBox, QSpinBox,
    QDialogButtonBox, QMessageBox, QAbstractItemView, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.widgets.common import SectionHeader, Separator, InfoBadge
from services.is_emri_service import IsEmriService
from models import IsEmri


class IsDetayDialog(QDialog):
    """İş emri detay ve düzenleme diyaloğu."""

    durum_guncellendi = pyqtSignal()

    def __init__(self, emri: IsEmri, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.emri = emri
        self.svc = IsEmriService()
        self.setWindowTitle(f"İş Emri Detayı — {emri.form_numarasi}")
        self.setMinimumSize(600, 480)
        self._build_ui()

    def _build_ui(self) -> None:
        """Detay dialog arayüzü."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Başlık
        title = QLabel(f"📋 {self.emri.form_numarasi}")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Bilgi grid
        grid = QGridLayout()
        grid.setSpacing(12)

        def add_row(row: int, label: str, value: str) -> None:
            lbl = QLabel(label)
            lbl.setObjectName("labelMuted")
            lbl.setFont(QFont("Segoe UI", 11))
            val = QLabel(value)
            val.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
            val.setWordWrap(True)
            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)

        add_row(0, "Müşteri:", self.emri.musteri_adi)
        add_row(1, "Malzeme:", self.emri.malzeme_cinsi)
        add_row(2, "Tarih:", self.emri.tarih)
        add_row(3, "Etiket Ölçüsü:", f"{self.emri.etiket_genisligi} x {self.emri.etiket_yuksekligi} mm")
        add_row(4, "Metraj:", f"{self.emri.metraj:,.1f} m")
        add_row(5, "Adet:", f"{self.emri.adet:,} adet")
        add_row(6, "Açıklama:", self.emri.aciklama or "—")

        # Durum
        lbl = QLabel("Durum:")
        lbl.setObjectName("labelMuted")
        lbl.setFont(QFont("Segoe UI", 11))
        grid.addWidget(lbl, 7, 0)

        badge = InfoBadge(self.emri.durum)
        grid.addWidget(badge, 7, 1)

        layout.addLayout(grid)

        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #334155;")
        layout.addWidget(sep)

        # Durum değiştirme
        durum_layout = QHBoxLayout()
        durum_lbl = QLabel("Durumu Değiştir:")
        durum_lbl.setFont(QFont("Segoe UI", 12))
        self.durum_combo = QComboBox()
        self.durum_combo.addItems([
            "Bekliyor", "Devam Ediyor", "Tamamlandı", "Hatalı Kesim"
        ])
        self.durum_combo.setCurrentText(self.emri.durum)
        durum_layout.addWidget(durum_lbl)
        durum_layout.addWidget(self.durum_combo)
        layout.addLayout(durum_layout)

        # Butonlar
        btn_box = QDialogButtonBox()
        update_btn = QPushButton("💾 Durumu Güncelle")
        update_btn.setObjectName("primaryBtn")
        update_btn.clicked.connect(self._update_durum)

        close_btn = QPushButton("✕ Kapat")
        close_btn.setObjectName("secondaryBtn")
        close_btn.clicked.connect(self.accept)

        delete_btn = QPushButton("🗑️ Sil")
        delete_btn.setObjectName("dangerBtn")
        delete_btn.setMinimumWidth(80)
        delete_btn.clicked.connect(self._delete)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addWidget(update_btn)
        layout.addLayout(btn_layout)

    def _update_durum(self) -> None:
        """Durumu günceller."""
        yeni_durum = self.durum_combo.currentText()
        self.svc.update_durum(self.emri.id, yeni_durum)  # type: ignore
        self.durum_guncellendi.emit()
        QMessageBox.information(self, "Güncellendi", f"Durum '{yeni_durum}' olarak güncellendi.")
        self.accept()

    def _delete(self) -> None:
        """İş emrini siler."""
        ret = QMessageBox.question(
            self, "Silme Onayı",
            f"'{self.emri.form_numarasi}' iş emrini silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret == QMessageBox.StandardButton.Yes:
            self.svc.delete(self.emri.id)  # type: ignore
            self.durum_guncellendi.emit()
            self.accept()


class IsKuyrukPage(QWidget):
    """İş kuyruğu sayfası."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.svc = IsEmriService()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Sayfa arayüzü."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Başlık
        header_row = QHBoxLayout()
        header = SectionHeader("📋 İş Kuyruğu", "Tüm iş emirleri")
        header_row.addWidget(header)
        header_row.addStretch()

        self.refresh_btn = QPushButton("🔄 Yenile")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(self.refresh_btn)

        layout.addLayout(header_row)
        layout.addWidget(Separator())

        # Filtre araç çubuğu
        filter_bar = self._build_filter_bar()
        layout.addWidget(filter_bar)

        # Tablo
        self.table = self._build_table()
        layout.addWidget(self.table)

        # Alt bilgi
        self.info_lbl = QLabel("0 kayıt")
        self.info_lbl.setObjectName("labelMuted")
        self.info_lbl.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.info_lbl)

    def _build_filter_bar(self) -> QFrame:
        """Filtre araç çubuğu."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Arama
        search_icon = QLabel("🔍")
        search_icon.setFont(QFont("Segoe UI Emoji", 14))
        layout.addWidget(search_icon)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Form no, müşteri veya malzeme ara...")
        self.search_edit.textChanged.connect(self._apply_filter)
        self.search_edit.setMinimumWidth(250)
        layout.addWidget(self.search_edit)

        # Durum filtresi
        durum_lbl = QLabel("Durum:")
        durum_lbl.setFont(QFont("Segoe UI", 12))
        layout.addWidget(durum_lbl)

        self.durum_filter = QComboBox()
        self.durum_filter.addItems([
            "Tümü", "Bekliyor", "Devam Ediyor", "Tamamlandı", "Hatalı Kesim"
        ])
        self.durum_filter.currentTextChanged.connect(self._apply_filter)
        layout.addWidget(self.durum_filter)

        layout.addStretch()
        return frame

    def _build_table(self) -> QTableWidget:
        """İş emri tablosunu oluşturur."""
        headers = [
            "Form No", "Tarih", "Müşteri", "Malzeme",
            "Etiket (mm)", "Metraj (m)", "Adet", "Durum", "Açıklama"
        ]
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setWordWrap(False)

        # Sütun genişlikleri
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        table.doubleClicked.connect(self._on_double_click)
        table.setMinimumHeight(400)
        return table

    def _apply_filter(self) -> None:
        """Filtre ve arama uygular."""
        query = self.search_edit.text().strip()
        durum = self.durum_filter.currentText()

        if query:
            emirler = self.svc.search(query)
            if durum != "Tümü":
                emirler = [e for e in emirler if e.durum == durum]
        else:
            emirler = self.svc.get_all(durum if durum != "Tümü" else None)

        self._populate_table(emirler)

    def _populate_table(self, emirler: list[IsEmri]) -> None:
        """Tabloyu iş emirleriyle doldurur."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(emirler))

        # Durum renkleri
        durum_colors = {
            "Bekliyor": ("#78350f", "#f59e0b"),
            "Devam Ediyor": ("#1e3a5f", "#3b82f6"),
            "Tamamlandı": ("#064e3b", "#10b981"),
            "Hatalı Kesim": ("#7f1d1d", "#ef4444"),
        }

        for row, emri in enumerate(emirler):
            cells = [
                emri.form_numarasi,
                emri.tarih,
                emri.musteri_adi,
                emri.malzeme_cinsi,
                f"{emri.etiket_genisligi:.0f}×{emri.etiket_yuksekligi:.0f}",
                f"{emri.metraj:,.1f}",
                f"{emri.adet:,}",
                emri.durum,
                emri.aciklama or "—",
            ]

            bg_dark, fg = durum_colors.get(emri.durum, ("#1e293b", "#94a3b8"))

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

                if col == 7:  # Durum sütunu
                    item.setForeground(QColor(fg))
                    item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

                # İş emri ID'sini UserRole'e sakla
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, emri.id)

                self.table.setItem(row, col, item)

            # Satır yüksekliği
            self.table.setRowHeight(row, 44)

        self.table.setSortingEnabled(True)
        self.info_lbl.setText(f"{len(emirler)} kayıt gösteriliyor")

    def _on_double_click(self, index) -> None:  # type: ignore
        """Çift tıklamada detay diyaloğunu açar."""
        row = index.row()
        item = self.table.item(row, 0)
        if not item:
            return

        emri_id = item.data(Qt.ItemDataRole.UserRole)
        emri = self.svc.get_by_id(emri_id)
        if not emri:
            return

        dialog = IsDetayDialog(emri, self)
        dialog.durum_guncellendi.connect(self.refresh)
        dialog.exec()

    def refresh(self) -> None:
        """Tabloyu yeniler."""
        self._apply_filter()
