# HOMTECH Duygu Analizi ve Akilli Ev Senaryo Sistemi

Bu proje, yuz goruntusunden duygu siniflandirmasi yaparak sonucuna gore HOMTECH benzeri bir akilli ev senaryo onerisi uretmek icin gelistirildi. Sistem; goruntu on isleme, TensorFlow/Keras tabanli model egitimi, tek gorsel uzerinden tahmin ve web arayuzunden senaryo gosterimi adimlarini bir araya getirir.

## Proje Ozeti

- FER-2013 veri seti ile 7 sinifli duygu tanima akisi kurulur.
- TensorFlow/Keras ile CNN tabanli model egitilir.
- Tek bir yuz fotografi uzerinden duygu tahmini yapilir.
- Tahmin sonucu, akilli ev davranis onerilerine donusturulur.
- Yerel web arayuzu ile sunum ve demo senaryolari calistirilabilir.

## Temel Ozellikler

- 7 duygu sinifi: `angry`, `disgust`, `fear`, `happy`, `sad`, `surprise`, `neutral`
- Grayscale `48x48` goruntu akisi
- Egitim, degerlendirme ve tahmin komutlari
- Sinif skorlarini ve akilli ev planini gosteren demo arayuzu
- Yuz tespitli veya tum gorsel uzerinden tahmin secenegi

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

## Klasor Yapisi

```text
YapayZekaModeli/
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|-- reports/
|-- src/
|   |-- data/
|   |-- models/
|   |-- web_demo/
|   |-- config.py
|   |-- demo_web.py
|   |-- evaluate.py
|   |-- image_preprocessing.py
|   |-- predict.py
|   |-- smart_home.py
|   |-- smart_home_demo.py
|   `-- train.py
|-- requirements.txt
`-- README.md
```

## Kurulum

TensorFlow tarafinda uyumluluk icin Python `3.12` kullanilmasi onerilir.

```powershell
uv venv --python 3.12 --seed .venv312
.\.venv312\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

Eger sanal ortam daha once hatali olustuysa yeniden kurabilirsin:

```powershell
Remove-Item -Recurse -Force .venv312
uv venv --python 3.12 --seed .venv312
.\.venv312\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## Veri Seti Hazirlama

FER-2013 veri setini Kaggle uzerinden indir:

`https://www.kaggle.com/datasets/msambare/fer2013`

Veri setini su yapida yerlestir:

```text
data/raw/fer2013/
|-- train/
`-- test/
```

Kontrol komutu:

```powershell
python -m src.data.check_fer2013
```

On isleme akisini dogrulamak icin:

```powershell
python -m src.data.inspect_preprocessing
```

## Model Egitimi

Ilk egitim denemesi icin:

```powershell
python -m src.train
```

Bu komut su ciktilari uretir:

- `artifacts/emotion_cnn.keras`
- `artifacts/training_history.csv`

## Degerlendirme

Egitilen modeli test etmek icin:

```powershell
python -m src.evaluate
```

Uretilen temel ciktilar:

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

## En Iyi Sonuc

Proje finalinde baz alinan en iyi test sonucu:

- `accuracy`: `0.5348`
- `precision`: `0.5417`
- `recall`: `0.5348`
- `weighted f1-score`: `0.5227`

## Tek Gorselle Tahmin

Tek bir gorsel uzerinden tahmin almak icin:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg"
```

Ornek kullanim:

```powershell
python -m src.predict --image "data/raw/fer2013/test/happy/PrivateTest_1071100.jpg"
```

Tum gorseli kullanmak icin:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg" --use-full-image
```

Akilli ev baglami ile tahmin:

```powershell
python -m src.predict --image "data/raw/fer2013/test/happy/PrivateTest_1071100.jpg" --time-of-day evening --occupancy family
```

## Akilli Ev Senaryo Demosu

Model calistirmadan dogrudan senaryo gostermek icin:

```powershell
python -m src.smart_home_demo --emotion sad --confidence 0.82 --time-of-day night --quiet-hours
```

Bu demo; aydinlatma, parlaklik, sicaklik, muzik profili, perde ve bildirim davranislarini kurala dayali olarak yorumlar.

## Web Arayuzu

Yerel demo arayuzunu baslatmak icin:

```powershell
python -m src.demo_web
```

Ardindan tarayicida su adresi ac:

`http://127.0.0.1:8000`

Arayuzde iki temel akis bulunur:

- `Senaryo`: Duygu ve ev baglamini elle secerek akilli ev sahnesi olusturur.
- `Gorsel Analizi`: Yuklenen yuz fotografi uzerinden tahmin yapar ve senaryo onerir.

## Projenin Amaci

Bu calisma, duygu analizi ile akilli ev otomasyonu arasinda uygulamali bir kopru kurmayi hedefler. Amac yalnizca bir siniflandirma modeli gelistirmek degil, modeli gercek hayata yaklastiran bir urun fikri ile birlestirmektir.
