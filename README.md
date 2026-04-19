# HOMTECH Duygu Analizi ve Akıllı Ev Senaryo Sistemi

Bu proje, yüz ifadesinden duygu tahmini yapıp sonucu HOMTECH benzeri bir akıllı ev senaryosuna dönüştüren bir demo ve sunum sistemidir. Yapı; görüntü ön işleme, TensorFlow/Keras tabanlı model eğitimi, tek görselle tahmin, açıklanabilir karar motoru, yerel web arayüzü, sunum modülü ve masaüstü uygulama akışlarını bir araya getirir.

## Proje Özeti

- FER-2013 veri seti ile 7 sınıflı duygu tanıma akışı kurulur.
- MobileNetV2 tabanlı transfer learning modeli eğitilir.
- Tek görsel üzerinden duygu tahmini yapılır.
- Tahmin sonucu ışık, sıcaklık, müzik, perde ve bildirim kararlarına çevrilir.
- Yerel web arayüzü ile hem canlı demo hem de sunum yapılabilir.
- İstenirse proje Windows masaüstü uygulaması olarak da paketlenebilir.

## Temel Özellikler

- 7 duygu sınıfı: `angry`, `disgust`, `fear`, `happy`, `sad`, `surprise`, `neutral`
- FER stiline yaklaştırılmış `96x96` RGB model girdisi
- Eğitim, değerlendirme ve tahmin komutları
- Senaryo modu ve gerçek görsel analizi modu
- Sunum için ayrı `/presentation` modülü
- Masaüstü uygulama launcher ve `.exe` build akışı

## Teknolojiler

- Python
- TensorFlow / Keras
- NumPy
- Pandas
- scikit-learn
- OpenCV
- Pillow
- Matplotlib
- Seaborn
- HTML / CSS / JavaScript
- pywebview
- PyInstaller

## Klasör Yapısı

```text
YapayZekaModeli/
|-- artifacts/
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|-- reports/
|-- scripts/
|   `-- generate_app_icon.py
|-- src/
|   |-- data/
|   |-- models/
|   |-- web_demo/
|   |   |-- index.html
|   |   |-- app.js
|   |   |-- styles.css
|   |   |-- presentation.html
|   |   |-- presentation.js
|   |   |-- presentation.css
|   |   |-- app_icon.png
|   |   `-- app_icon.ico
|   |-- config.py
|   |-- demo_web.py
|   |-- desktop_app.py
|   |-- evaluate.py
|   |-- image_preprocessing.py
|   |-- predict.py
|   |-- presentation_data.py
|   |-- smart_home.py
|   |-- smart_home_demo.py
|   `-- train.py
|-- build_desktop.ps1
|-- requirements.txt
|-- requirements-desktop.txt
|-- start_demo.ps1
|-- start_desktop.ps1
`-- README.md
```

## Kurulum

TensorFlow tarafında uyumluluk için Python `3.12` önerilir.

```powershell
uv venv --python 3.12 --seed .venv312
.\.venv312\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

Desktop uygulama tarafı için ek bağımlılıklar:

```powershell
uv pip install --python .\.venv312\Scripts\python.exe -r requirements-desktop.txt
```

## Veri Seti Hazırlama

FER-2013 veri setini Kaggle üzerinden indir:

`https://www.kaggle.com/datasets/msambare/fer2013`

Veri setini şu yapıda yerleştir:

```text
data/raw/fer2013/
|-- train/
`-- test/
```

Kontrol komutları:

```powershell
python -m src.data.check_fer2013
python -m src.data.inspect_preprocessing
```

## Model Eğitimi

```powershell
python -m src.train
```

Bu komut başlıca şu çıktıları üretir:

- `artifacts/emotion_cnn.keras`
- `artifacts/training_history.csv`

## Değerlendirme

```powershell
python -m src.evaluate
```

Üretilen temel çıktılar:

- `accuracy`
- `precision`
- `recall`
- `f1-score`
- classification report
- confusion matrix

Kaydedilen dosyalar:

- `artifacts/confusion_matrix.png`
- `artifacts/confusion_matrix.csv`
- `artifacts/classification_report.txt`

## Referans Sonuç

Proje finalinde baz alınan en iyi test sonucu:

- `accuracy`: `0.5348`
- `precision`: `0.5417`
- `recall`: `0.5348`
- `weighted f1-score`: `0.5227`

## Tek Görselle Tahmin

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg"
```

Tam görsel kullanımı:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg" --use-full-image
```

Akıllı ev bağlamı ile:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg" --time-of-day evening --occupancy family
```

## Akıllı Ev Senaryo Demosu

Model çalıştırmadan doğrudan senaryo göstermek için:

```powershell
python -m src.smart_home_demo --emotion sad --confidence 0.82 --time-of-day night --quiet-hours
```

Bu akış; aydınlatma, parlaklık, sıcaklık, müzik, perde ve bildirim davranışlarını kural tabanlı olarak yorumlar.

## Web Arayüzü

Yerel demo arayüzünü başlatmak için en pratik yol:

```powershell
.\start_demo.ps1
```

Alternatif:

```powershell
python -m src.demo_web
```

Açılacak adresler:

- Demo paneli: `http://127.0.0.1:8000/`
- Sunum modülü: `http://127.0.0.1:8000/presentation`

Arayüzde iki temel akış bulunur:

- `Senaryo`: Duygu ve ev bağlamını elle seçerek akıllı ev sahnesi oluşturur.
- `Görsel Analizi`: Yüklenen yüz fotoğrafı üzerinden tahmin yapar ve senaryo önerir.

Sunum modülünde:

- veri seti özeti
- teknoloji yığını
- model metrikleri
- confusion matrix
- ürün fikri ve sistem akışı

tek bir localhost yapısı içinde gösterilebilir.

## Masaüstü Uygulama

Projeyi tarayıcı yerine kendi penceresinde açmak için:

```powershell
.\start_desktop.ps1
```

Windows `.exe` build almak için:

```powershell
.\build_desktop.ps1
```

Build çıktısı:

- `dist/HOMTECHMoodConsole/HOMTECHMoodConsole.exe`

Not: PyInstaller çıktısında yalnızca `.exe` değil, tüm `dist/HOMTECHMoodConsole` klasörü birlikte taşınmalıdır.

## Projenin Amacı

Bu çalışma, duygu analizi ile akıllı ev otomasyonu arasında uygulamalı bir köprü kurmayı hedefler. Amaç yalnızca bir sınıflandırma modeli geliştirmek değil, modeli gerçek hayata yaklaşan bir ürün deneyimi ile birleştirmektir.
