"""
VD3350 Manager - Fire Yönetimi Sayfası
=========================================
Fire ve hata kayıtlarının girişi ve görüntülenmesi.

DÜZELTME: FOREIGN KEY constraint failed hatası düzeltildi.
form_numarasi boş girildiğinde veya is_emirleri tablosunda
bulunmayan bir değer girildiğinde None olarak kaydediliyordu.
Artık:
1. Form no alanı boş bırakılabilir → None olarak kaydedilir
2. Girilen form no veritabanında kontrol edilir, yoksa None kullanılır
3. Kullanıcıya açık hata mesajı gösterilir
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
        list_title = QLabel("📋 Fire Kayıtları")
        list_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        content_layout.addWidget(list_title)
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

        # Form No — ComboBox ile mevcut iş emirlerinden seçim
        grid.addWidget(lbl("Form Numarası"), 0, 0)
        self.form_no_combo = QComboBox()
        self.form_no_combo.setEditable(True)
        self.form_no_combo.lineEdit().setPlaceholderText(  # type: ignore
            "Boş bırakabilirsiniz (opsiyonel)..."
        )
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
            "ℹ️  Form numarası opsiyoneldir. Yalnızca veritabanında kayıtlı "
            "form numaraları seçilebilir. Hatalı Metre ve Hatalı Adet alanları "
            "bağımsızdır; sadece metre, sadece adet veya ikisi birlikte girilebilir."
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

    def _populate_table(self, kayitlar: list) -> None:
        """Tabloyu doldurur."""
        self.table.setRowCount(len(kayitlar))
        for row, k in enumerate(kayitlar):
            metre_str = f"{k.hatali_metre:.2f} m" if k.hatali_metre else "—"
            adet_str = f"{k.hatali_adet:,} adet" if k.hatali_adet else "—"
            cells = [
                str(row + 1),
                k.form_numarasi or "—",
                k.tarih,
                metre_str,
                adet_str,
                k.fire_nedeni or "—",
                k.aciklama or "—",
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                )
                self.table.setItem(row, col, item)
            self.table.setRowHeight(row, 36)

    def _refresh_form_no_list(self) -> None:
        """İş emirleri listesini yeniler (FOREIGN KEY için geçerli değerler)."""
        try:
            self.form_no_combo.blockSignals(True)
            current_text = self.form_no_combo.currentText()
            self.form_no_combo.clear()
            self.form_no_combo.addItem("")  # Boş seçenek (NULL için)
            emirler = self.is_svc.get_all()
            for emri in emirler:
                self.form_no_combo.addItem(
                    f"{emri.form_numarasi} — {emri.musteri_adi}"
                )
            # Önceki değeri koru
            idx = self.form_no_combo.findText(current_text)
            if idx >= 0:
                self.form_no_combo.setCurrentIndex(idx)
            elif current_text:
                self.form_no_combo.setCurrentText(current_text)
            self.form_no_combo.blockSignals(False)
        except Exception:
            self.form_no_combo.blockSignals(False)

    def _get_form_no(self) -> Optional[str]:
        """
        Girilen form numarasını döner.
        DÜZELTME: FOREIGN KEY hatasını önlemek için:
        1. Boş giriş → None
        2. "FORM — MÜŞTERİ" formatında giriş → form_no kısmını al
        3. Girilen değer DB'de yoksa → None (ve kullanıcıya uyarı)
        """
        text = self.form_no_combo.currentText().strip()

        # Boş → None (FOREIGN KEY ihlali yok)
        if not text:
            return None

        # "IE20240101001 — Müşteri" formatından form_no'yu ayıkla
        if " — " in text:
            form_no = text.split(" — ")[0].strip()
        else:
            form_no = text

        # Veritabanında var mı kontrol et
        emri = self.is_svc.get_by_form_no(form_no)
        if emri:
            return form_no
        elif text:
            # Kullanıcı var olmayan bir form no girmiş
            ret = QMessageBox.question(
                self,
                "Form Numarası Bulunamadı",
                f"'{form_no}' numaralı iş emri veritabanında bulunamadı.\n\n"
                f"Form numarasız olarak kaydetmek ister misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if ret == QMessageBox.StandardButton.Yes:
                return None
            else:
                return "IPTAL"  # İptal işareti

        return None

    def _save(self) -> None:
        """Fire kaydını veritabanına kaydeder."""
        # Form No — FOREIGN KEY hatası için özel işleme
        form_no = self._get_form_no()
        if form_no == "IPTAL":
            return  # Kullanıcı iptal etti

        hatali_metre = self.metre_spin.value() if self.metre_spin.value() > 0 else None
        hatali_adet = self.adet_spin.value() if self.adet_spin.value() > 0 else None

        # En az biri girilmeli
        if hatali_metre is None and hatali_adet is None:
            QMessageBox.warning(
                self, "Uyarı",
                "En az bir değer girilmelidir:\n"
                "• Hatalı Metre\n"
                "• Hatalı Adet"
            )
            return

        tarih = self.tarih_edit.date().toString("yyyy-MM-dd")
        neden = self.neden_combo.currentText()
        aciklama = self.aciklama_edit.text().strip()

        kayit = FireKaydi(
            form_numarasi=form_no,  # None olabilir — FOREIGN KEY ihlali yok
            tarih=tarih,
            hatali_metre=hatali_metre,
            hatali_adet=hatali_adet,
            fire_nedeni=neden,
            aciklama=aciklama,
        )

        try:
            self.fire_svc.create(kayit)
            # Formu sıfırla
            self.form_no_combo.setCurrentIndex(0)
            self.metre_spin.setValue(0)
            self.adet_spin.setValue(0)
            self.aciklama_edit.clear()
            self.refresh()
            QMessageBox.information(
                self, "✅ Kaydedildi",
                f"Fire kaydı başarıyla eklendi.\n"
                f"Form: {form_no or '(bağlantısız)'}\n"
                f"Metre: {hatali_metre or '—'}\n"
                f"Adet: {hatali_adet or '—'}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Kayıt Hatası",
                f"Fire kaydı eklenirken hata oluştu:\n{e}\n\n"
                f"İpucu: Form numarası veritabanında kayıtlı olmalıdır "
                f"veya boş bırakılmalıdır."
            )

    def refresh(self) -> None:
        """Sayfayı yeniler."""
        try:
            # Form no listesini güncelle
            self._refresh_form_no_list()

            # Kayıtları getir
            kayitlar = self.fire_svc.get_all()
            self._populate_table(kayitlar)

            # İstatistikleri güncelle
            toplam_fire = sum(
                k.hatali_metre for k in kayitlar if k.hatali_metre
            )
            self.toplam_fire_lbl.setText(
                f"🗑️  Toplam Fire: {toplam_fire:.2f} m"
            )
            self.kayit_sayisi_lbl.setText(
                f"📋  Toplam Kayıt: {len(kayitlar)}"
            )

            # En çok görülen neden
            nedenler = self.fire_svc.get_fire_nedenleri()
            if nedenler:
                en_cok = nedenler[0]
                self.en_cok_neden_lbl.setText(
                    f"📌  En Çok: {en_cok['fire_nedeni']} ({en_cok['adet']}x)"
                )
            else:
                self.en_cok_neden_lbl.setText("📌  En Çok: —")

        except Exception as e:
            pass
