"""
VD3350 Manager - Dashboard Sayfası
=====================================
Ana kontrol paneli: istatistik kartları ve üretim grafikleri.
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

from ui.widgets.common import StatCard, SectionHeader, Separator
from services.is_emri_service import IsEmriService
from services.fire_service import FireService
from services.bicak_service import BicakService


class DashboardPage(QWidget):
    """Ana dashboard sayfası."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.is_emri_svc = IsEmriService()
        self.fire_svc = FireService()
        self.bicak_svc = BicakService()
        self._is_dark = True
        self._build_ui()
        self._start_refresh_timer()

    def _build_ui(self) -> None:
        """Ana layout oluşturur."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(24)

        # Başlık
        header = SectionHeader(
            "📊 Dashboard",
            "Günlük üretim özeti ve makine durumu"
        )
        main_layout.addWidget(header)
        main_layout.addWidget(Separator())

        # Scroll alanı
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # İstatistik kartları
        self.stat_grid = QGridLayout()
        self.stat_grid.setSpacing(16)
        self._build_stat_cards()
        content_layout.addLayout(self.stat_grid)

        # Grafik bölümü
        if MATPLOTLIB_OK:
            charts_layout = QHBoxLayout()
            charts_layout.setSpacing(16)

            self.production_chart = self._build_production_chart()
            self.fire_chart = self._build_fire_chart()
            self.material_chart = self._build_material_chart()

            charts_layout.addWidget(self.production_chart, 3)
            charts_layout.addWidget(self.fire_chart, 2)
            charts_layout.addWidget(self.material_chart, 2)
            content_layout.addLayout(charts_layout)
        else:
            no_chart = QLabel("📈 Grafikler için 'matplotlib' kütüphanesini yükleyin.")
            no_chart.setObjectName("labelMuted")
            no_chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(no_chart)

        # Bıçak durumu özeti
        content_layout.addWidget(self._build_blade_summary())
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _build_stat_cards(self) -> None:
        """İstatistik kartlarını oluşturur."""
        self.stat_cards: dict[str, StatCard] = {
            "gunluk_is": StatCard(
                "Günlük Kesilen İş", "0", "adet", "✂️", "#3b82f6"
            ),
            "gunluk_metraj": StatCard(
                "Günlük Metraj", "0 m", "metre", "📏", "#10b981"
            ),
            "gunluk_fire": StatCard(
                "Toplam Fire", "0 m", "hatalı metre", "🗑️", "#ef4444"
            ),
            "fire_orani": StatCard(
                "Fire Oranı", "%0.0", "günlük", "📉", "#f97316"
            ),
            "ort_uretim": StatCard(
                "Ort. Günlük Üretim", "0 m", "son 30 gün", "📈", "#8b5cf6"
            ),
            "hatali_kesim": StatCard(
                "Hatalı Kesim", "0", "bugün", "⚠️", "#f59e0b"
            ),
        }

        positions = [
            (0, 0), (0, 1), (0, 2),
            (1, 0), (1, 1), (1, 2),
        ]
        keys = list(self.stat_cards.keys())
        for i, (row, col) in enumerate(positions):
            self.stat_grid.addWidget(self.stat_cards[keys[i]], row, col)

        self.stat_grid.setColumnStretch(0, 1)
        self.stat_grid.setColumnStretch(1, 1)
        self.stat_grid.setColumnStretch(2, 1)

    def _build_production_chart(self) -> QFrame:
        """Son 30 gün üretim grafiği."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("📈 Son 30 Gün Üretim (Metre)")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        fig = Figure(figsize=(5, 3), tight_layout=True)
        fig.patch.set_facecolor("none")
        self.prod_ax = fig.add_subplot(111)
        self.prod_canvas = FigureCanvas(fig)
        self.prod_canvas.setMinimumHeight(200)
        layout.addWidget(self.prod_canvas)

        self._update_production_chart()
        return frame

    def _build_fire_chart(self) -> QFrame:
        """Fire grafiği."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("🗑️ Fire Grafiği")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        fig = Figure(figsize=(3.5, 3), tight_layout=True)
        fig.patch.set_facecolor("none")
        self.fire_ax = fig.add_subplot(111)
        self.fire_canvas = FigureCanvas(fig)
        self.fire_canvas.setMinimumHeight(200)
        layout.addWidget(self.fire_canvas)

        self._update_fire_chart()
        return frame

    def _build_material_chart(self) -> QFrame:
        """Malzeme kullanım grafiği."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("🧾 Malzeme Kullanımı")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        fig = Figure(figsize=(3.5, 3), tight_layout=True)
        fig.patch.set_facecolor("none")
        self.mat_ax = fig.add_subplot(111)
        self.mat_canvas = FigureCanvas(fig)
        self.mat_canvas.setMinimumHeight(200)
        layout.addWidget(self.mat_canvas)

        self._update_material_chart()
        return frame

    def _build_blade_summary(self) -> QFrame:
        """Bıçak kafası durum özeti kartı."""
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 16, 20, 16)

        title = QLabel("🔪 Bıçak Kafası Durumu")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        self.blade_layout = QHBoxLayout()
        self.blade_layout.setSpacing(12)
        layout.addLayout(self.blade_layout)

        self._update_blade_summary()
        return frame

    def _update_production_chart(self) -> None:
        """Üretim grafiğini günceller."""
        if not MATPLOTLIB_OK:
            return
        data = self.is_emri_svc.get_son_30_gun_uretim()
        ax = self.prod_ax
        ax.clear()

        if data:
            dates = [d["tarih"][-5:] for d in data]  # MM-DD
            values = [d["toplam_metraj"] for d in data]

            color = "#3b82f6"
            ax.fill_between(range(len(dates)), values, alpha=0.2, color=color)
            ax.plot(range(len(dates)), values, color=color, linewidth=2.5, marker="o", markersize=4)

            step = max(1, len(dates) // 7)
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], fontsize=9)
        else:
            ax.text(0.5, 0.5, "Henüz veri yok", ha="center", va="center",
                    fontsize=12, alpha=0.5, transform=ax.transAxes)

        self._style_ax(ax)
        if hasattr(self, "prod_canvas"):
            self.prod_canvas.draw()

    def _update_fire_chart(self) -> None:
        """Fire grafiğini günceller."""
        if not MATPLOTLIB_OK:
            return
        data = self.fire_svc.get_son_30_gun_fire()
        ax = self.fire_ax
        ax.clear()

        if data:
            dates = [d["tarih"][-5:] for d in data]
            values = [d["toplam_fire"] or 0 for d in data]
            color = "#ef4444"
            ax.bar(range(len(dates)), values, color=color, alpha=0.8, width=0.7)
            step = max(1, len(dates) // 5)
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], fontsize=9)
        else:
            ax.text(0.5, 0.5, "Henüz fire yok", ha="center", va="center",
                    fontsize=12, alpha=0.5, transform=ax.transAxes)

        self._style_ax(ax)
        if hasattr(self, "fire_canvas"):
            self.fire_canvas.draw()

    def _update_material_chart(self) -> None:
        """Malzeme kullanım pasta grafiğini günceller."""
        if not MATPLOTLIB_OK:
            return
        data = self.is_emri_svc.get_malzeme_kullanim()
        ax = self.mat_ax
        ax.clear()

        if data:
            labels = [d["malzeme_cinsi"] for d in data]
            values = [d["toplam_metraj"] for d in data]
            colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444",
                      "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]
            wedges, texts, autotexts = ax.pie(
                values, labels=None, colors=colors[:len(values)],
                autopct="%1.0f%%", startangle=90, pctdistance=0.7,
            )
            for t in autotexts:
                t.set_fontsize(8)
                t.set_color("white")
            ax.legend(wedges, labels, loc="lower center", fontsize=8,
                      ncol=2, frameon=False)
        else:
            ax.text(0.5, 0.5, "Henüz veri yok", ha="center", va="center",
                    fontsize=12, alpha=0.5, transform=ax.transAxes)

        self._style_ax(ax)
        if hasattr(self, "mat_canvas"):
            self.mat_canvas.draw()

    def _style_ax(self, ax) -> None:  # type: ignore
        """Grafik ekseni stilini ayarlar (dark/light tema)."""
        bg = "#1e293b" if self._is_dark else "#ffffff"
        fg = "#94a3b8" if self._is_dark else "#64748b"
        ax.set_facecolor("none")
        for spine in ax.spines.values():
            spine.set_color("#334155" if self._is_dark else "#e2e8f0")
        ax.tick_params(colors=fg, labelsize=9)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)

    def _update_blade_summary(self) -> None:
        """Bıçak kafaları özetini günceller."""
        # Mevcut widget'ları temizle
        while self.blade_layout.count():
            item = self.blade_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        kafalar = self.bicak_svc.get_all()
        for kafa in kafalar:
            kalan = kafa.kalan_yuzdesi
            renk = kafa.durum_rengi

            card = QFrame()
            card.setObjectName("card")
            card.setMinimumWidth(100)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(12, 10, 12, 10)
            c_layout.setSpacing(6)
            c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Kafa no
            kafa_lbl = QLabel(f"Kafa {kafa.kafa_no}")
            kafa_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            kafa_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(kafa_lbl)

            # Kalan yüzde
            pct_lbl = QLabel(f"%{kalan:.0f}")
            pct_lbl.setFont(QFont("Segoe UI", 18, QFont.Weight.ExtraBold))
            pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pct_lbl.setStyleSheet(f"color: {renk}; background: transparent; border: none;")
            c_layout.addWidget(pct_lbl)

            # Metre
            metre_lbl = QLabel(f"{kafa.toplam_kesilen_metre:,.0f} m")
            metre_lbl.setObjectName("labelMuted")
            metre_lbl.setFont(QFont("Segoe UI", 10))
            metre_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            c_layout.addWidget(metre_lbl)

            # Durum etiketi
            durum_lbl = QLabel(kafa.durum)
            durum_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            durum_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            durum_lbl.setStyleSheet(
                f"color: {renk}; background: {renk}22; border: 1px solid {renk}66; "
                f"border-radius: 6px; padding: 2px 8px;"
            )
            c_layout.addWidget(durum_lbl)

            self.blade_layout.addWidget(card)

        self.blade_layout.addStretch()

    def refresh(self, is_dark: bool = True) -> None:
        """Tüm dashboard verilerini yeniler."""
        self._is_dark = is_dark
        stats = self.is_emri_svc.get_dashboard_stats()

        self.stat_cards["gunluk_is"].update_value(str(stats["gunluk_is"]))
        self.stat_cards["gunluk_metraj"].update_value(f"{stats['gunluk_metraj']:,.0f} m")
        self.stat_cards["gunluk_fire"].update_value(f"{stats['gunluk_fire']:,.1f} m")
        self.stat_cards["fire_orani"].update_value(f"%{stats['fire_orani']:.1f}")
        self.stat_cards["ort_uretim"].update_value(f"{stats['ort_uretim']:,.0f} m")
        self.stat_cards["hatali_kesim"].update_value(str(stats["hatali_kesim"]))

        if MATPLOTLIB_OK:
            self._update_production_chart()
            self._update_fire_chart()
            self._update_material_chart()

        self._update_blade_summary()

    def _start_refresh_timer(self) -> None:
        """5 dakikada bir otomatik yenileme."""
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.refresh(self._is_dark))
        timer.start(300_000)  # 5 dakika
