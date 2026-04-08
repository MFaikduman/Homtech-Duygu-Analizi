# HOMTECH Duygu Tabanli Akilli Ev Modu Oneri Sistemi

Bu proje, yuz goruntusunden duygu siniflandirmasi yapip sonucuna gore HOMTECH akilli ev modu onerisi uretmek icin hazirlanmistir.

## Proje Akisi

1. FER-2013 veri setini hazirla
2. Veri on isleme yap
3. TensorFlow/Keras ile modeli kur
4. Modeli egit
5. Test ve metrikleri al
6. Webcam veya ornek gorsellerle tahmin yap
7. Rapor ozeti, yontem ve sonuc metni olustur

## Klasor Yapisi

```text
YapayZekaModeli/
|-- .vscode/
|-- data/
|   |-- raw/
|   `-- processed/
|-- artifacts/
|-- notebooks/
|-- reports/
|-- src/
|   |-- data/
|   |-- models/
|   |-- config.py
|   |-- train.py
|   |-- evaluate.py
|   `-- predict.py
|-- requirements.txt
`-- README.md
```

## Gerekli Kutuphaneler

- tensorflow
- numpy
- pandas
- matplotlib
- seaborn
- scikit-learn
- opencv-python
- pillow
- kagglehub

## Onemli Not

TensorFlow'un resmi kurulum sayfasina gore Windows uzerinde desteklenen Python surumleri 3.10-3.13 araligindadir. Bu nedenle proje icin Python 3.12 kullanmamiz en guvenli secimdir.

## Ilk Kurulum Adimlari

PowerShell terminalinde sirayla su komutlari calistir:

```powershell
uv venv --python 3.12 --seed .venv312
.\.venv312\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

Eger `.venv312` klasorunu daha once `--seed` olmadan olusturduysan, once eski klasoru silip yeniden olustur:

```powershell
Remove-Item -Recurse -Force .venv312
uv venv --python 3.12 --seed .venv312
.\.venv312\Scripts\Activate.ps1
uv pip install -r requirements.txt
```

## FER-2013 Ilk Adim

1. Kaggle uzerinden FER-2013 veri setini indir:
   `https://www.kaggle.com/datasets/msambare/fer2013`
2. Icindeki klasorleri su yapida yerlestir:

```text
data/raw/fer2013/
|-- train/
`-- test/
```

3. Sonra veri setini kontrol et:

```powershell
python -m src.data.check_fer2013
```

Bu komut sinif klasorlerini ve goruntu sayilarini ekrana yazar.

## Veri On Isleme Ilk Adim

Bu projede FER-2013 gorsellerini TensorFlow ile dogrudan klasorlerden okuyacagiz.

- Goruntu boyutu: `48x48`
- Renk modu: `grayscale`
- Etiketleme: klasor adina gore otomatik
- Batch boyutu: `64`

Veri yukleme kontrolu icin su komutu calistir:

```powershell
python -m src.data.inspect_preprocessing
```

Beklenen temel sonuc:

- `train` ve `test` verisi yuklenmeli
- Goruntu batch sekli `(64, 48, 48, 1)` olmali
- Etiket batch sekli `(64, 7)` olmali
- Piksel araligi `0-255` gorunmeli

Bu adim tamamlandiginda bir sonraki asamada veri artirma ve model egitimi icin hazir olacagiz.

## Model Kurma ve Ilk Egitim

Bu asamada temel bir CNN modeli kullaniyoruz.

- Giris boyutu: `48x48x1`
- Cikis sinifi: `7`
- Kayip fonksiyonu: `categorical_crossentropy`
- Basari metrigi: `accuracy`

Ilk egitim denemesi icin terminalde su komutu calistir:

```powershell
python -m src.train
```

Bu komut:

- veri setini yukler
- temel CNN modelini kurar
- egitimi baslatir
- en iyi modeli `artifacts/emotion_cnn.keras` dosyasina kaydeder
- egitim gecmisini `artifacts/training_history.csv` dosyasina yazar

Not: Ilk egitim CPU'da zaman alabilir. Bu normaldir.

## Test ve Metrikler

Egitim tamamlandiktan sonra modeli test etmek icin su komutu calistir:

```powershell
python -m src.evaluate
```

Bu komut su ciktilari uretir:

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

Projede finalize edilen en iyi test sonucu su sekildedir:

- `accuracy`: `0.5348`
- `precision`: `0.5417`
- `recall`: `0.5348`
- `weighted f1-score`: `0.5227`

Not: Daha sonra dengeli ornekleme ve transfer learning tabanli ek denemeler yapildi. Ancak bu denemeler mevcut en iyi sonucu gecemedigi icin proje finalinde yukaridaki degerler esas alinmistir.

## Tek Gorselle Tahmin

Egitilmis modeli kullanarak tek bir yuz gorselinden tahmin almak icin su komutu calistir:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg"
```

Ornek:

```powershell
python -m src.predict --image "data/raw/fer2013/test/happy/PrivateTest_1071100.jpg"
```

Bu komut sunlari verir:

- tahmin edilen duygu
- guven skoru
- sinif olasiliklari
- onerilen HOMTECH modu

Varsayilan davranis:

- once yuz algilamaya calisir
- yuz bulursa yuz bolgesiyle tahmin yapar
- yuz bulamazsa tum gorseli kullanir

Eger yuz algilamayi kapatmak istersen:

```powershell
python -m src.predict --image "ornek_gorsel_yolu.jpg" --use-full-image
```

`predict` komutu yalnizca duygu etiketi vermez; ayni zamanda zaman, ev dolulugu ve sessiz saat baglamina gore akilli ev aksiyon plani da uretir.

Ornek:

```powershell
python -m src.predict --image "data/raw/fer2013/test/happy/PrivateTest_1071100.jpg" --time-of-day evening --occupancy family
```

## Akilli Ev Demo

Model tahmini olmadan dogrudan senaryo gostermek icin su komut kullanilabilir:

```powershell
python -m src.smart_home_demo --emotion sad --confidence 0.82 --time-of-day night --quiet-hours
```

Bu komut duygu bilgisini su cihaz davranislarina donusturur:

- aydinlatma sahnesi
- parlaklik seviyesi
- sicaklik onerisi
- muzik profili
- perde konumu
- bildirim politikasi
- otomasyonun dogrudan uygulanip uygulanmayacagi

## Gorsel Arayuz Demo

Hocaya sunum icin yerel web arayuzunu su komutla baslat:

```powershell
python -m src.demo_web
```

Ardindan tarayicida `http://127.0.0.1:8000` adresini ac.

Bu demo arayuzunde iki farkli akis vardir:

- `Senaryo`: duygu, guven ve ev baglamini elle secip anlik HOMTECH sahnesi gosterir
- `Gorsel Analizi`: bir yuz fotografi yukleyip modeli calistirir, sinif skorlarini ve akilli ev planini ekrana yansitir
