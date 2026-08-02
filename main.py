#!/usr/bin/env python3
"""
VD3350 Manager — Gündoğdu Kağıt
=====================================
VD3350 Etiket Kesim Plotter Makinesi Üretim Yönetim Uygulaması

Kullanım:
    python main.py

Gereksinimler:
    pip install -r requirements.txt
"""

import sys
import os

# Proje kök dizinini Python yoluna ekle
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap

# Splash ekranı sınıfı
class SplashScreen(QSplashScreen):
    """Uygulama açılış ekranı."""

    def __init__(self) -> None:
        # 600x340 piksel gradient splash
        pixmap = QPixmap(600, 340)
        pixmap.fill(QColor("#0f172a"))
        
        # HATA DÜZELTİLDİ: Çizimi QSplashScreen'e resmi vermeden ÖNCE, doğrudan asıl obje üzerine yapıyoruz.
        self._draw_content(pixmap)
        
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)

    def _draw_content(self, pixmap: QPixmap) -> None:
        from PyQt6.QtGui import QPainter, QLinearGradient
        from PyQt6.QtCore import QRect, QPoint

        painter = QPainter(pixmap)

        # Gradient arka plan
        gradient = QLinearGradient(0, 0, 600, 340)
        gradient.setColorAt(0, QColor("#0f172a"))
        gradient.setColorAt(0.5, QColor("#1e3a5f"))
        gradient.setColorAt(1, QColor("#0f172a"))
        painter.fillRect(0, 0, 600, 340, gradient)

        # Logo metni
        painter.setPen(QColor("#3b82f6"))
        painter.setFont(QFont("Segoe UI", 48, QFont.Weight.ExtraBold))
        painter.drawText(QRect(0, 60, 600, 100), Qt.AlignmentFlag.AlignCenter, "VD3350")

        painter.setPen(QColor("#e2e8f0"))
        painter.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        painter.drawText(QRect(0, 150, 600, 50), Qt.AlignmentFlag.AlignCenter, "Manager")

        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Segoe UI", 13))
        painter.drawText(QRect(0, 205, 600, 30), Qt.AlignmentFlag.AlignCenter, "Gündoğdu Kağıt — Etiket Kesim Yönetim Sistemi")

        painter.setPen(QColor("#475569"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(QRect(0, 295, 600, 30), Qt.AlignmentFlag.AlignCenter, "Yükleniyor...")

        painter.end()


def main() -> None:
    """Ana uygulama başlatıcısı."""

    # High DPI desteği
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("VD3350 Manager")
    app.setApplicationDisplayName("VD3350 Manager — Gündoğdu Kağıt")
    app.setOrganizationName("Gündoğdu Kağıt")
    app.setOrganizationDomain("gundogdukagit.com")

    # Sistem font
    font = QFont("Segoe UI", 12)
    app.setFont(font)

    # Splash ekranı
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Veritabanı başlat
    splash.showMessage(
        "  Veritabanı başlatılıyor...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor("#64748b"),
    )
    app.processEvents()

    from database import db  # noqa: F401 - DB bağlantısını başlat

    # Ana pencere
    splash.showMessage(
        "  Arayüz yükleniyor...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor("#64748b"),
    )
    app.processEvents()

    from ui.main_window import MainWindow
    window = MainWindow()

    # Splash kapat, pencere aç
    QTimer.singleShot(1200, lambda: _show_main(splash, window))

    sys.exit(app.exec())


def _show_main(splash: QSplashScreen, window: "MainWindow") -> None:
    """Splash ekranını kapatıp ana pencereyi gösterir."""
    # window = MainWindow() ifadesi zaten yukarıda belleğe alındı, gösterim işlemi yapılıyor.
    splash.finish(window)
    window.showMaximized()


if __name__ == "__main__":
    main()