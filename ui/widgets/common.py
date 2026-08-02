"""
VD3350 Manager - Common UI Widgets
=====================================
Tekrar kullanılabilir özel widget bileşenleri.
"""

from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor


class StatCard(QFrame):
    """
    Dashboard istatistik kartı.
    İkon, başlık, değer ve alt başlık gösterir.
    """

    clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        icon: str = "📊",
        accent_color: str = "#3b82f6",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.accent_color = accent_color
        self.setObjectName("statCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(120)
        self._build_ui(title, value, subtitle, icon)
        self._add_shadow()

    def _build_ui(self, title: str, value: str, subtitle: str, icon: str) -> None:
        """Widget içeriğini oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        # Üst satır: ikon + başlık
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 18))
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            f"background: {self.accent_color}22; border-radius: 10px; "
            f"color: {self.accent_color}; border: none;"
        )

        title_lbl = QLabel(title)
        title_lbl.setObjectName("labelMuted")
        title_lbl.setFont(QFont("Segoe UI", 11))

        top_row.addWidget(icon_lbl)
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Değer
        self.value_lbl = QLabel(value)
        self.value_lbl.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(
            f"color: {self.accent_color}; background: transparent; border: none;"
        )
        layout.addWidget(self.value_lbl)

        # Alt başlık
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("labelMuted")
            sub_lbl.setFont(QFont("Segoe UI", 11))
            layout.addWidget(sub_lbl)

    def _add_shadow(self) -> None:
        """Gölge efekti ekler."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)

    def update_value(self, value: str) -> None:
        """Değer etiketini günceller."""
        self.value_lbl.setText(value)

    def mousePressEvent(self, event) -> None:  # type: ignore
        """Tıklama sinyali gönderir."""
        self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:  # type: ignore
        """Hover efekti."""
        self.setStyleSheet(
            f"QFrame#statCard {{ border-color: {self.accent_color}; }}"
        )
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore
        """Hover efekti kaldır."""
        self.setStyleSheet("")
        super().leaveEvent(event)


class SectionHeader(QWidget):
    """Sayfa bölüm başlığı."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("pageTitle")
        title_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("pageSubTitle")
            sub_lbl.setFont(QFont("Segoe UI", 12))
            layout.addWidget(sub_lbl)


class Separator(QFrame):
    """Yatay ayırıcı çizgi."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("hLine")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(1)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )


class InfoBadge(QLabel):
    """Durum badge etiketi."""

    STATUS_COLORS: dict[str, tuple[str, str]] = {
        "Bekliyor": ("#f59e0b", "#78350f"),
        "Devam Ediyor": ("#3b82f6", "#1e3a5f"),
        "Tamamlandı": ("#10b981", "#064e3b"),
        "Hatalı Kesim": ("#ef4444", "#7f1d1d"),
        "Normal": ("#10b981", "#064e3b"),
        "İyi": ("#3b82f6", "#1e3a5f"),
        "Uyarı": ("#f59e0b", "#78350f"),
        "Kritik": ("#ef4444", "#7f1d1d"),
    }

    def __init__(
        self,
        status: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(status, parent)
        self._apply_style(status)

    def _apply_style(self, status: str) -> None:
        """Duruma göre stil uygular."""
        fg, bg = self.STATUS_COLORS.get(status, ("#94a3b8", "#1e293b"))
        self.setStyleSheet(
            f"color: {fg}; background: {bg}44; border: 1px solid {fg}66; "
            f"border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 600;"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(status)

    def set_status(self, status: str) -> None:
        """Durumu günceller."""
        self._apply_style(status)


class LoadingOverlay(QWidget):
    """Yükleme katmanı."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: rgba(0,0,0,0.5); border-radius: 12px;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel("⏳ Yükleniyor...")
        lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        self.hide()

    def show_loading(self) -> None:
        """Yükleme katmanını gösterir."""
        self.resize(self.parent().size())  # type: ignore
        self.show()
        self.raise_()

    def hide_loading(self) -> None:
        """Yükleme katmanını gizler."""
        self.hide()


class EmptyState(QWidget):
    """Boş veri durumu gösterici."""

    def __init__(
        self,
        icon: str = "📋",
        title: str = "Veri Bulunamadı",
        subtitle: str = "",
        action_text: str = "",
        action_callback: Optional[Callable] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 48))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setObjectName("labelMuted")
            sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub_lbl.setFont(QFont("Segoe UI", 12))
            layout.addWidget(sub_lbl)

        if action_text and action_callback:
            btn = QPushButton(action_text)
            btn.setObjectName("primaryBtn")
            btn.setFixedWidth(180)
            btn.clicked.connect(action_callback)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
