"""
VD3350 Manager - Ana Pencere
================================
Uygulamanın ana penceresi: sidebar navigasyon ve sayfa yönetimi.
"""

import os
import sys
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget,
    QStatusBar, QButtonGroup, QMessageBox, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QIcon

from ui.pages.dashboard import DashboardPage
from ui.pages.is_emri_page import IsEmriForm
from ui.pages.is_kuyrugu_page import IsKuyrukPage
from ui.pages.operaror_panel import OperatorPanel
from ui.pages.fire_page import FireYonetimPage
from ui.pages.bicak_page import BicakTakipPage
from ui.pages.rulo_page import RuloPage
from ui.pages.rapor_page import RaporPage
from ui.pages.ayarlar_page import AyarlarPage
from database import db


# Sayfa tanımları: (simge, ad, sınıf)
NAV_ITEMS = [
    ("📊", "Dashboard", DashboardPage),
    ("➕", "Yeni İş Emri", IsEmriForm),
    ("📋", "İş Kuyruğu", IsKuyrukPage),
    ("🎮", "Operatör Paneli", OperatorPanel),
    ("🗑️", "Fire Yönetimi", FireYonetimPage),
    ("✂️", "Bıçak Takibi", BicakTakipPage),
    ("🎯", "Rulo Hesaplama", RuloPage),
    ("📊", "Raporlar", RaporPage),
    ("⚙️", "Ayarlar", AyarlarPage),
]


class BackupThread(QThread):
    """Arka planda veritabanı yedekleme thread'i."""

    backup_done = pyqtSignal(str)

    def run(self) -> None:
        try:
            path = db.backup()
            self.backup_done.emit(path)
        except Exception as e:
            self.backup_done.emit(f"HATA: {e}")


class SidebarButton(QPushButton):
    """Sidebar navigasyon butonu."""

    def __init__(self, icon: str, label: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarBtn")
        self.setText(f"  {icon}  {label}")
        self.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        self.setMinimumHeight(44)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class MainWindow(QMainWindow):
    """
    Ana uygulama penceresi.
    Sol sidebar navigasyon + sağ içerik alanı (QStackedWidget).
    """

    def __init__(self) -> None:
        super().__init__()
        self._is_dark_theme = True
        self._pages: dict[int, QWidget] = {}
        self.setWindowTitle("VD3350 Manager — Gündoğdu Kağıt")
        self.setMinimumSize(1280, 760)
        self._load_theme(dark=True)
        self._build_ui()
        # self._connect_signals() satırı kaldırıldı
        self._setup_status_bar()
        self._start_timers()
        # İlk sayfa: Dashboard
        self._navigate_to(0)

    # =========================================================
    # UI Oluşturma
    # =========================================================

    def _build_ui(self) -> None:
        """Ana pencere layout'ını oluşturur."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # Sağ taraf: Header + İçerik
        right_side = QVBoxLayout()
        right_side.setContentsMargins(0, 0, 0, 0)
        right_side.setSpacing(0)

        right_side.addWidget(self._build_header())

        # İçerik alanı
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")
        right_side.addWidget(self.stack)

        main_layout.addLayout(right_side, 1)

    def _build_sidebar(self) -> QFrame:
        """Sol navigasyon sidebar'ını oluşturur."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo / Marka
        logo_widget = QWidget()
        logo_widget.setFixedHeight(70)
        logo_widget.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "stop:0 #1e3a5f, stop:1 #0f172a);"
        )
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(20, 12, 20, 12)
        logo_layout.setSpacing(0)

        app_name = QLabel("VD3350")
        app_name.setFont(QFont("Segoe UI", 18, QFont.Weight.ExtraBold))
        app_name.setStyleSheet("color: #3b82f6; background: transparent; border: none;")

        sub_name = QLabel("Gündoğdu Kağıt")
        sub_name.setFont(QFont("Segoe UI", 9))
        sub_name.setStyleSheet("color: #64748b; background: transparent; border: none;")

        logo_layout.addWidget(app_name)
        logo_layout.addWidget(sub_name)
        layout.addWidget(logo_widget)

        # Ayırıcı
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #1e293b; border: none;")
        layout.addWidget(line)

        # Boşluk
        layout.addSpacing(8)

        # Navigasyon menü etiketi
        menu_lbl = QLabel("  MENÜ")
        menu_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        menu_lbl.setStyleSheet("color: #475569; background: transparent; border: none; letter-spacing: 1px;")
        menu_lbl.setFixedHeight(24)
        layout.addWidget(menu_lbl)

        # Nav butonları
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[SidebarButton] = []

        for i, (icon, label, _) in enumerate(NAV_ITEMS):
            btn = SidebarButton(icon, label)
            self.nav_group.addButton(btn, i)
            btn.clicked.connect(lambda checked, idx=i: self._navigate_to(idx))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # Alt: Tema değiştir & Yedekle
        bottom_sep = QFrame()
        bottom_sep.setFixedHeight(1)
        bottom_sep.setStyleSheet("background: #1e293b; border: none;")
        layout.addWidget(bottom_sep)

        self.theme_btn = QPushButton("🌙  Koyu Tema")
        self.theme_btn.setObjectName("sidebarBtn")
        self.theme_btn.setFont(QFont("Segoe UI", 11))
        self.theme_btn.setMinimumHeight(40)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        self.backup_btn = QPushButton("💾  Veritabanı Yedekle")
        self.backup_btn.setObjectName("sidebarBtn")
        self.backup_btn.setFont(QFont("Segoe UI", 11))
        self.backup_btn.setMinimumHeight(40)
        self.backup_btn.clicked.connect(self._do_backup)
        layout.addWidget(self.backup_btn)

        layout.addSpacing(8)
        return sidebar

    def _build_header(self) -> QFrame:
        """Üst header bar."""
        header = QFrame()
        header.setObjectName("headerWidget")
        header.setFixedHeight(60)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(12)

        # Sayfa başlığı (dinamik)
        self.header_title = QLabel("📊 Dashboard")
        self.header_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(self.header_title)

        layout.addStretch()

        # Saat
        self.clock_lbl = QLabel()
        self.clock_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        self.clock_lbl.setStyleSheet(
            "color: #64748b; background: transparent; border: none;"
        )
        layout.addWidget(self.clock_lbl)

        # Bildirim
        self.notif_lbl = QLabel("🔔")
        self.notif_lbl.setFont(QFont("Segoe UI Emoji", 16))
        self.notif_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.notif_lbl)

        return header

    # =========================================================
    # Navigasyon
    # =========================================================

    def _navigate_to(self, index: int) -> None:
        """Belirtilen sayfa indeksine geçer."""
        # Sayfayı lazy-load et
        if index not in self._pages:
            _, label, PageClass = NAV_ITEMS[index]
            page = PageClass()
            self._pages[index] = page
            self.stack.addWidget(page)
            self._wire_page_signals(index, page)

        self.stack.setCurrentWidget(self._pages[index])

        # Buton durumu
        self.nav_buttons[index].setChecked(True)

        # Header güncelle
        icon, label, _ = NAV_ITEMS[index]
        self.header_title.setText(f"{icon} {label}")

        # Sayfayı yenile
        self._refresh_page(index)

    def _wire_page_signals(self, index: int, page: QWidget) -> None:
        """Sayfa sinyallerini bağlar."""
        if isinstance(page, IsEmriForm):
            page.is_kaydedildi.connect(self._on_is_kaydedildi)
        elif isinstance(page, OperatorPanel):
            page.is_guncellendi.connect(self._on_is_guncellendi)
        elif isinstance(page, AyarlarPage):
            page.kagit_listesi_guncellendi.connect(self._on_kagit_guncellendi)

    def _refresh_page(self, index: int) -> None:
        """Aktif sayfayı yeniler."""
        page = self._pages.get(index)
        if page and hasattr(page, "refresh"):
            if isinstance(page, DashboardPage):
                page.refresh(self._is_dark_theme)
            else:
                page.refresh()  # type: ignore

    # =========================================================
    # Sinyal İşleyicileri
    # =========================================================

    def _on_is_kaydedildi(self) -> None:
        """İş emri kaydedilince kuyruğu yenile."""
        if 2 in self._pages:
            self._pages[2].refresh()  # type: ignore
        self._check_notifications()

    def _on_is_guncellendi(self) -> None:
        """Operatör paneli güncellemesi."""
        if 2 in self._pages:
            self._pages[2].refresh()  # type: ignore
        if 0 in self._pages:
            self._pages[0].refresh(self._is_dark_theme)  # type: ignore
        self._check_notifications()

    def _on_kagit_guncellendi(self) -> None:
        """Kağıt listesi güncellenince form ve rulo sayfalarını yenile."""
        if 1 in self._pages:
            self._pages[1].refresh()  # type: ignore
        if 6 in self._pages:
            self._pages[6].refresh()  # type: ignore

    # =========================================================
    # Tema
    # =========================================================

    def _load_theme(self, dark: bool = True) -> None:
        """Tema QSS dosyasını yükler ve uygular."""
        theme_file = "dark_theme.qss" if dark else "light_theme.qss"
        styles_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "styles"
        )
        qss_path = os.path.join(styles_dir, theme_file)
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        db.set_setting("theme", "dark" if dark else "light")

    def _toggle_theme(self) -> None:
        """Koyu/Açık tema değiştirir."""
        self._is_dark_theme = not self._is_dark_theme
        self._load_theme(self._is_dark_theme)

        if self._is_dark_theme:
            self.theme_btn.setText("☀️  Açık Tema")
        else:
            self.theme_btn.setText("🌙  Koyu Tema")

        # Dashboard grafiklerini yenile
        if 0 in self._pages:
            self._pages[0].refresh(self._is_dark_theme)  # type: ignore

    # =========================================================
    # Status Bar
    # =========================================================

    def _setup_status_bar(self) -> None:
        """Alt durum çubuğunu ayarlar."""
        sb = self.statusBar()
        if sb:
            sb.showMessage(
                "VD3350 Manager hazır | Gündoğdu Kağıt | "
                f"Veritabanı: {db._connection is not None and 'Bağlı' or 'Bağlantı Yok'}"
            )

    # =========================================================
    # Zamanlayıcılar
    # =========================================================

    def _start_timers(self) -> None:
        """Periyodik işlemler için zamanlayıcılar başlatır."""
        # Saat güncelleme (her saniye)
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Bildirim kontrolü (her 5 dakika)
        self._notif_timer = QTimer(self)
        self._notif_timer.timeout.connect(self._check_notifications)
        self._notif_timer.start(300_000)
        self._check_notifications()

        # Otomatik yedekleme (saatte bir)
        self._backup_timer = QTimer(self)
        self._backup_timer.timeout.connect(self._auto_backup)
        self._backup_timer.start(3_600_000)

    def _update_clock(self) -> None:
        """Saat etiketini günceller."""
        now = datetime.now().strftime("%d.%m.%Y  %H:%M:%S")
        self.clock_lbl.setText(now)

    def _check_notifications(self) -> None:
        """Kritik bıçak ve yüksek fire uyarılarını kontrol eder."""
        from services.bicak_service import BicakService
        svc = BicakService()
        kritikler = svc.get_kritik_kafalar()

        notifications: list[str] = []
        for k in kritikler:
            notifications.append(
                f"⚠️ Kafa {k.kafa_no} kritik: %{k.kalan_yuzdesi:.0f} kalan ömür!"
            )

        if notifications:
            self.notif_lbl.setToolTip("\n".join(notifications))
            self.notif_lbl.setText("🔔🔴")
        else:
            self.notif_lbl.setToolTip("Bildirim yok")
            self.notif_lbl.setText("🔔")

        # Status bar
        sb = self.statusBar()
        if sb and notifications:
            sb.showMessage(notifications[0], 10_000)

    def _do_backup(self) -> None:
        """Manuel yedekleme."""
        self.backup_thread = BackupThread()
        self.backup_thread.backup_done.connect(self._on_backup_done)
        self.backup_thread.start()
        self.backup_btn.setText("⏳ Yedekleniyor...")
        self.backup_btn.setEnabled(False)

    def _auto_backup(self) -> None:
        """Otomatik yedekleme (sessiz)."""
        try:
            db.backup()
        except Exception:
            pass

    def _on_backup_done(self, path: str) -> None:
        """Yedekleme tamamlanınca bildirir."""
        self.backup_btn.setText("💾  Veritabanı Yedekle")
        self.backup_btn.setEnabled(True)
        if path.startswith("HATA"):
            QMessageBox.critical(self, "Yedekleme Hatası", path)
        else:
            sb = self.statusBar()
            if sb:
                sb.showMessage(f"✅ Yedek alındı: {path}", 8_000)
