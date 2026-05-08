# HOMTECH Duygu Analizi ve Akilli Ev Senaryo Sistemi

HOMTECH, yuz ifadesinden duygu tahmini yapan ve bu sonucu akilli ev senaryolarina ceviren bir Python projesidir. Proje; TensorFlow/Keras modeli, FER-2013 veri setiyle egitim-degerlendirme akisi, tek gorselden tahmin, yerel web demo arayuzu ve opsiyonel Windows masaustu paketleme adimlarini icerir.

Bu repo bir `npm` projesi degildir. Web arayuzu Python'un yerel HTTP sunucusu uzerinden calisir.

## Teknolojiler

- Python 3.12
- TensorFlow / Keras
- NumPy, Pandas
- scikit-learn
- OpenCV
- Pillow
- Matplotlib, Seaborn
- HTML / CSS / JavaScript
- Opsiyonel: pywebview, PyInstaller

## Hizli Baslangic

Komutlari `README.md` ve `requirements.txt` dosyalarinin bulundugu repo kokunde calistirin.

```powershell
git clone https://github.com/MFaikduman/Homtech-Duygu-Analizi.git
cd Homtech-Duygu-Analizi
uv venv --python 3.12 --seed .venv312
.\.venv312\Scripts\Activate.ps1
uv pip install -r requirements.txt
python -m src.demo_web
```

Tarayicida su adresi acin:

```text
http://127.0.0.1:8000
```

Windows icin hazir baslatma scripti de kullanilabilir:

```powershell
.\start_demo.ps1
```

PowerShell script calistirmayi engellerse:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_demo.ps1
```

> Not: Ilk kurulumdan sonra web demo acilir. Egitilmis model yoksa gorsel analiz modu model isteyebilir; senaryo modu model olmadan calisir.

## macOS / Linux Kurulum

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m src.demo_web
```

## Veri Seti

Model egitimi ve gorsel tahmin icin FER-2013 veri seti gerekir:

```text
https://www.kaggle.com/datasets/msambare/fer2013
```

Veri setini su klasor yapisiyla yerlestirin:

```text
data/raw/fer2013/
|-- train/
|   |-- angry/
|   |-- disgust/
|   |-- fear/
|   |-- happy/
|   |-- neutral/
|   |-- sad/
|   `-- surprise/
`-- test/
    |-- angry/
    |-- disgust/
    |-- fear/
    |-- happy/
    |-- neutral/
    |-- sad/
    `-- surprise/
```

Veri setini kontrol etmek icin:

```powershell
python -m src.data.check_fer2013
```

## Model Egitimi

```powershell
python -m src.train
```

Egitim tamamlandiginda baslica su dosyalar olusur:

- `artifacts/emotion_cnn.keras`
- `artifacts/training_history.csv`

Modeli degerlendirmek icin:

```powershell
python -m src.evaluate
```

Degerlendirme su dosyalari uretebilir:

- `artifacts/confusion_matrix.png`
- `artifacts/confusion_matrix.csv`
- `artifacts/classification_report.txt`

## Tek Gorselle Tahmin

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg"
```

Yuz algilama yerine gorselin tamamini kullanmak icin:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg" --use-full-image
```

Baglam parametreleriyle:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg" --time-of-day evening --occupancy family --quiet-hours
```

## Senaryo Modu

Model calistirmadan akilli ev senaryosu uretmek icin:

```powershell
python -m src.smart_home_demo --emotion sad --confidence 0.82 --time-of-day night --quiet-hours
```

## Kalite Kontrolleri

Kaynak kodun import/syntax kontrolu:

```powershell
python -m compileall -q src
```

Hafif smoke testleri:

```powershell
python -m unittest discover -s tests
```

Bagimlilik uyumlulugu:

```powershell
uv pip check --python .\.venv312\Scripts\python.exe
```

GitHub Actions, `main` branch'ine push veya pull request geldiginde ayni compile ve smoke test akisini calistirir.

## Web Demo

```powershell
python -m src.demo_web
```

Adresler:

- Demo paneli: `http://127.0.0.1:8000/`
- Sunum modu: `http://127.0.0.1:8000/presentation`
- Saglik kontrolu: `http://127.0.0.1:8000/api/health`

## Opsiyonel Masaustu Uygulama

Masaustu uygulama web demoyu kendi penceresinde acar. Bu akis GitHub'dan calistirma icin zorunlu degildir.

```powershell
uv pip install -r requirements-desktop.txt
.\start_desktop.ps1
```

Windows `.exe` paketi almak icin:

```powershell
.\build_desktop.ps1
```

Cikti klasoru:

```text
dist/HOMTECHMoodConsole/
```

## Proje Yapisi

```text
.
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- sample_images/
|-- notebooks/
|-- reports/
|-- scripts/
|-- tests/
|-- src/
|   |-- data/
|   |-- models/
|   |-- web_demo/
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
|-- requirements.txt
|-- requirements-desktop.txt
|-- pyproject.toml
|-- start_demo.ps1
|-- start_desktop.ps1
|-- build_desktop.ps1
`-- README.md
```

## GitHub Notlari

- Python surumu `.python-version` ile `3.12` olarak sabitlendi.
- Paket metadata ve konsol scriptleri `pyproject.toml` icinde tutulur.
- `main` branch'i icin `.github/workflows/ci.yml` smoke test workflow'u vardir.
- Gercek API key, token veya parola gerekmiyor; bu nedenle `.env.example` dosyasina ihtiyac yok.
- `.env`, sanal ortamlar, cache klasorleri, FER-2013 veri seti, egitilmis model/artifact dosyalari ve PyInstaller build ciktilari repoya eklenmemelidir.
- `data/raw/`, `data/processed/`, `data/sample_images/`, `artifacts/`, `reports/` ve `notebooks/` klasorleri `.gitkeep` dosyalariyla bos halde tutulabilir.
- Egitilmis model dosyasi buyuk oldugu icin GitHub'a koymak yerine `python -m src.train` ile yerelde uretin.

## Sorun Giderme

- `Egitilmis model bulunamadi` hatasi: `python -m src.train` ile modeli egitin veya web demoda senaryo modunu kullanin.
- TensorFlow kurulum sorunu: Python 3.12 kullandiginizdan emin olun.
- PowerShell script hatasi: `powershell -ExecutionPolicy Bypass -File .\start_demo.ps1` komutunu deneyin.
- Veri seti bulunamadi hatasi: FER-2013 klasorlerini `data/raw/fer2013/` altina yerlestirin.
