"""
VD3350 Manager - Database Layer
================================
SQLite veritabanı bağlantısı ve tablo yönetimi.
Tüm veritabanı işlemleri bu modül üzerinden yapılır.
"""

import sqlite3
import os
import shutil
from datetime import datetime
from typing import Optional, Any
import threading


# Veritabanı dosyasının yolu
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "vd3350.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")


class DatabaseManager:
    """
    Singleton pattern ile SQLite veritabanı yöneticisi.
    Thread-safe bağlantı havuzu sağlar.
    """

    _instance: Optional["DatabaseManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        os.makedirs(DB_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
        self._seed_default_data()

    def _connect(self) -> None:
        """Veritabanı bağlantısını açar."""
        self._connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")

    @property
    def conn(self) -> sqlite3.Connection:
        """Aktif bağlantıyı döner."""
        if self._connection is None:
            self._connect()
        return self._connection  # type: ignore

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Parametreli SQL sorgusu çalıştırır."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
            return cursor

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        """Çok satırlı sorgu sonucu döner."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Tek satırlı sorgu sonucu döner."""
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()

    def _create_tables(self) -> None:
        """Tüm tabloları oluşturur."""
        sql_statements = [
            """
            CREATE TABLE IF NOT EXISTS is_emirleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_numarasi TEXT NOT NULL UNIQUE,
                tarih TEXT NOT NULL,
                musteri_adi TEXT NOT NULL,
                malzeme_cinsi TEXT NOT NULL,
                etiket_genisligi REAL NOT NULL,
                etiket_yuksekligi REAL NOT NULL,
                metraj REAL NOT NULL,
                adet INTEGER NOT NULL,
                durum TEXT NOT NULL DEFAULT 'Bekliyor',
                aciklama TEXT,
                olusturulma_tarihi TEXT NOT NULL,
                guncellenme_tarihi TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS fire_ve_hatalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_numarasi TEXT,
                tarih TEXT NOT NULL,
                hatali_metre REAL,
                hatali_adet INTEGER,
                fire_nedeni TEXT,
                aciklama TEXT,
                FOREIGN KEY (form_numarasi) REFERENCES is_emirleri(form_numarasi)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS makine_presetleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                malzeme_cinsi TEXT NOT NULL UNIQUE,
                gramaj REAL,
                kalinlik_micron REAL,
                ideal_hiz REAL,
                bicak_basinci REAL,
                ccd_hassasiyeti REAL,
                olusturma_tarihi TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bicak_kafalari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kafa_no INTEGER NOT NULL UNIQUE,
                takilan_uc_tarihi TEXT NOT NULL,
                toplam_kesilen_metre REAL NOT NULL DEFAULT 0,
                tahmini_omur REAL NOT NULL DEFAULT 35000,
                durum TEXT NOT NULL DEFAULT 'Normal'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS kagit_turleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL UNIQUE,
                kalinlik_micron REAL NOT NULL,
                aciklama TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rulo_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                malzeme TEXT NOT NULL,
                baslangic_metre REAL,
                kalan_metre REAL,
                cevre_cm REAL NOT NULL,
                hesaplanan_metre REAL NOT NULL,
                tarih TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
        ]
        for sql in sql_statements:
            self.execute(sql)

    def _seed_default_data(self) -> None:
        """Varsayılan verileri ekler (ilk çalıştırmada)."""
        # Bıçak kafalarını oluştur (6 adet)
        for kafa_no in range(1, 7):
            existing = self.fetchone(
                "SELECT id FROM bicak_kafalari WHERE kafa_no = ?", (kafa_no,)
            )
            if not existing:
                self.execute(
                    """INSERT INTO bicak_kafalari
                       (kafa_no, takilan_uc_tarihi, toplam_kesilen_metre, tahmini_omur, durum)
                       VALUES (?, ?, 0, 35000, 'Normal')""",
                    (kafa_no, datetime.now().strftime("%Y-%m-%d")),
                )

        # Varsayılan kağıt türleri
        default_papers = [
            ("Kuşe", 80.0, "Parlak kaplamalı kağıt"),
            ("PP Opak", 60.0, "Polipropilen opak film"),
            ("PP Şeffaf", 50.0, "Polipropilen şeffaf film"),
            ("Termal", 65.0, "Termal etiket kağıdı"),
            ("PE", 70.0, "Polietilen film"),
            ("Selefonlu", 90.0, "Selefon kaplamalı kağıt"),
            ("Kraft", 100.0, "Kraft kağıt"),
            ("Beyaz PP", 55.0, "Beyaz polipropilen"),
        ]
        for isim, kalinlik, aciklama in default_papers:
            existing = self.fetchone(
                "SELECT id FROM kagit_turleri WHERE isim = ?", (isim,)
            )
            if not existing:
                self.execute(
                    "INSERT INTO kagit_turleri (isim, kalinlik_micron, aciklama) VALUES (?, ?, ?)",
                    (isim, kalinlik, aciklama),
                )

        # Varsayılan makine presetleri
        default_presets = [
            ("Kuşe", 80.0, 80.0, 10.0, 72.0, 5.0),
            ("PP Opak", 60.0, 60.0, 11.0, 85.0, 4.0),
            ("PP Şeffaf", 50.0, 50.0, 12.0, 80.0, 4.0),
            ("Termal", 65.0, 65.0, 9.0, 70.0, 5.0),
            ("PE", 70.0, 70.0, 10.0, 75.0, 5.0),
            ("Selefonlu", 90.0, 90.0, 8.0, 78.0, 5.0),
        ]
        for malzeme, gramaj, kalinlik, hiz, basinc, ccd in default_presets:
            existing = self.fetchone(
                "SELECT id FROM makine_presetleri WHERE malzeme_cinsi = ?", (malzeme,)
            )
            if not existing:
                self.execute(
                    """INSERT INTO makine_presetleri
                       (malzeme_cinsi, gramaj, kalinlik_micron, ideal_hiz, bicak_basinci, ccd_hassasiyeti, olusturma_tarihi)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        malzeme,
                        gramaj,
                        kalinlik,
                        hiz,
                        basinc,
                        ccd,
                        datetime.now().strftime("%Y-%m-%d"),
                    ),
                )

        # Varsayılan tema ayarı
        existing = self.fetchone("SELECT key FROM app_settings WHERE key = 'theme'")
        if not existing:
            self.execute(
                "INSERT INTO app_settings (key, value) VALUES ('theme', 'dark')"
            )

    def backup(self) -> str:
        """Veritabanını yedekler ve yedek dosya yolunu döner."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"vd3350_backup_{timestamp}.db")
        shutil.copy2(DB_PATH, backup_path)
        return backup_path

    def get_setting(self, key: str, default: str = "") -> str:
        """Ayar değerini okur."""
        row = self.fetchone("SELECT value FROM app_settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Ayar değerini kaydeder."""
        self.execute(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, value),
        )

    def close(self) -> None:
        """Veritabanı bağlantısını kapatır."""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global veritabanı örneği
db = DatabaseManager()
