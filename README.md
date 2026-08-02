# VD3350 Manager — Gündoğdu Kağıt

**VD3350 Etiket Kesim (Plotter) Makinesi Üretim Yönetim Uygulaması**

---

## 🚀 Kurulum

### 1. Python 3.12+ Gereksinimi
```bash
python --version  # 3.12+ olmalı
```

### 2. Bağımlılıkları Yükle
```bash
cd VD3350_Manager
pip install -r requirements.txt
```

### 3. Uygulamayı Başlat
```bash
python main.py
```

---

## 📦 Proje Yapısı

```
VD3350_Manager/
│
├── main.py                 # Uygulama giriş noktası
├── database.py             # SQLite veritabanı katmanı (Singleton)
├── models.py               # Veri modelleri (dataclass)
│
├── services/
│   ├── is_emri_service.py  # İş emri iş mantığı
│   ├── fire_service.py     # Fire kayıt iş mantığı
│   ├── bicak_service.py    # Bıçak takip iş mantığı
│   └── preset_service.py   # Preset ve kağıt türleri
│
├── ui/
│   ├── main_window.py      # Ana pencere
│   ├── pages/
│   │   ├── dashboard.py    # Ana dashboard
│   │   ├── is_emri_page.py # Yeni iş emri formu
│   │   ├── is_kuyrugu_page.py # İş kuyruğu
│   │   ├── operaror_panel.py  # Hızlı operatör paneli
│   │   ├── fire_page.py    # Fire yönetimi
│   │   ├── bicak_page.py   # Bıçak takip sistemi
│   │   ├── rulo_page.py    # Rulo hesaplama
│   │   ├── rapor_page.py   # Raporlama
│   │   └── ayarlar_page.py # Ayarlar
│   └── widgets/
│       └── common.py       # Ortak widget bileşenleri
│
├── assets/
│   └── styles/
│       ├── dark_theme.qss  # Koyu tema
│       └── light_theme.qss # Açık tema
│
├── database/
│   └── vd3350.db           # SQLite veritabanı (otomatik oluşur)
│       └── backups/        # Otomatik yedekler
│
├── requirements.txt
└── README.md
```

---

## ✨ Özellikler

### 📊 Dashboard
- Günlük kesilen iş sayısı
- Günlük metraj
- Toplam fire ve fire oranı
- Son 30 gün üretim grafiği
- Fire grafiği
- Malzeme kullanım pasta grafiği
- Bıçak kafası durum özeti

### ➕ Yeni İş Emri
- Form numarası otomatik üretimi
- Malzeme seçimine göre preset bilgisi otomatik gösterimi
- Kaydetme sonrası otomatik kuyruğa ekleme

### 📋 İş Kuyruğu
- Arama ve filtreleme
- Durum bazlı renklendirme
- Çift tıkla detay/düzenleme

### 🎮 Hızlı Operatör Paneli
- **✅ Temiz Bitti** — İşi tamamlar, metrajı kaydeder
- **⚠️ Sıyırma Koptu** — +2m fire ekler, işi tamamlar
- **❌ Kamera Hatası** — Hatalı kesim, fire kaydeder
- Canlı iş bitiş sayacı

### 🗑️ Fire Yönetimi
- Hatalı metre ve adet bağımsız giriş
- Fire nedeni seçimi
- İstatistik özeti

### ✂️ Bıçak Takip Sistemi
- 6 kafa, 2 istasyon görsel takibi
- Renk kodlu ömür göstergesi (Yeşil/Sarı/Turuncu/Kırmızı)
- Tek tık ile sıfırlama
- Kritik bıçak bildirimleri

### 🎯 Rulo Hesaplama
- Çevre → metre otomatik hesaplama
- Malzeme bazlı kalınlık otomatik doldurma
- Geçmiş kayıt

### 📊 Raporlama
- Günlük/haftalık/aylık filtre
- PDF ve Excel dışa aktarma
- Top müşteri, malzeme, fire nedeni listeleri

### ⚙️ Ayarlar
- Kağıt türleri yönetimi
- Makine presetleri yönetimi
- Koyu/Açık tema değiştirme
- Otomatik veritabanı yedekleme

---

## 🎨 Tasarım
- Modern Flat Design
- Microsoft Fluent Design ilhamı
- Koyu/Açık tema desteği
- QSS StyleSheet
- Kart (Card) yapısı
- Gradient header

---

## 🛠️ Teknik Detaylar

- **Python 3.12+**
- **PyQt6** — GUI framework
- **SQLite** — Yerel veritabanı
- **Matplotlib** — Grafikler
- **ReportLab** — PDF çıktısı
- **OpenPyXL** — Excel çıktısı
- **MVC Mimarisi** — UI / Service / Database katmanları
- **OOP & SOLID** prensipleri
- **Type Hints** kullanımı
- **Thread-safe** veritabanı bağlantısı

---

## 📋 Veritabanı Tabloları

| Tablo | Açıklama |
|-------|----------|
| `is_emirleri` | İş emirleri ve kesim geçmişi |
| `fire_ve_hatalar` | Fire ve hata kayıtları |
| `makine_presetleri` | Malzemeye göre makine ayarları |
| `bicak_kafalari` | Bıçak kafası ömür takibi |
| `kagit_turleri` | Kağıt/malzeme türleri |
| `rulo_gecmisi` | Rulo çevre hesaplama geçmişi |
| `app_settings` | Uygulama ayarları |

---

© 2024 Gündoğdu Kağıt — VD3350 Manager
