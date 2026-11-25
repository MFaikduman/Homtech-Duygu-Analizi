# HOMTECH EmotionAI — klasik makine öğrenmesi

Projenin ana yöntemi **HOG + PCA + RBF SVM**. Varsayılan profil altı yüz
ifadesini kapsar. Önceki derin öğrenme altyapısı
`archive/classical-ml-transition-2026-11-17/` altında bulunur.

## Yöntem

1. RAF-DB'nin hizalanmış yüz görselleri gri tona çevrilir.
2. Görseller 96×96 boyutuna getirilir ve histogram eşitlemesi uygulanır.
3. HOG ile yerel kenar yönleri çıkarılır. Varsayılan ayarlar 12 yön kutusu,
   8×8 piksel hücre, 16×16 blok ve 8×8 blok adımıdır. Her görsel 5.808 özellik üretir.
4. StandardScaler özellikleri eğitim bölümünden öğrendiği istatistiklerle ölçekler.
5. PCA, HOG özelliklerini eğitim bölümünden öğrendiği 128 bileşene indirger.
6. RBF SVM, C=1 ve `class_weight="balanced"` ile altı ifade sınıfını öğrenir.
   Birden fazla C verilirse seçim doğrulama macro F1 skoruyla yapılır.

Bu akış klasik makine öğrenmesidir: HOG elle tasarlanmış bir özellik çıkarıcıdır;
öğrenilen sınıflandırıcı SVM'dir. Epoch, ağırlık dondurma veya GPU kurulumu yoktur.
Klasik yöntem ve derin öğrenme sonuçları aynı başarı beklentisiyle sunulmaz.

## Veri ve deney protokolü

- Resmî BasicEmo eğitim kümesi: 12.271 görsel.
- Resmî test kümesi: 3.068 görsel.
- Altı sınıflı varsayılan profilde eğitim 9.824, doğrulama 1.730 ve test 2.908 görsel içerir.
- Ayrım `--seed 42` ile tekrar üretilebilir; kimlikler manifestte tutulur.
- HOG özellikleri eğitim sırasında yalnızca eğitim/doğrulama için çıkarılır.
- StandardScaler, PCA ve SVM yalnızca eğitim bölümünden öğrenir.
- Test verisi model/C seçimi için kullanılmaz; içerik fingerprint'i manifestte saklanır.
- Bu örnek bazlı ayrımdır; kişi kimliği bazında genelleme garantisi değildir.

Varsayılan modelin sınıf sırası `angry, fear, happy, sad, surprise, neutral`.
`disgust` eğitim, doğrulama ve test için filtrelenir. Veri denetimi ve
`seven-linear` profili, RAF-DB'nin yedi sınıflı kapsamını kullanır.

## Konumlar

[Veri klasörleri](../data/README.md) ve [proje yapısı](../README.md).

- Özgün indirme: `data/downloads/rafdb/basic/`.
- Hazır etiket: `data/raw/rafdb/BasicEmo/EmoLabel/list_patition_label.txt`.
- Hazır yüzler: `data/raw/rafdb/BasicEmo/Image/aligned/`.
- Veri raporu: `artifacts/datasets/rafdb-audit.json`.
- Varsayılan eğitim koşusu: `artifacts/runs/six-class-rbf-001/`.
- Eski TensorFlow/Caffe: `archive/legacy-2026-11-17/`.
- Önceki PyTorch hattı: `archive/classical-ml-transition-2026-11-17/`.

## Çalıştırma

```powershell
uv sync --locked
uv run --no-sync homtech-check-data --verify-images --output artifacts/datasets/rafdb-audit.json
uv run --no-sync homtech-train --output-dir artifacts/runs/six-class-rbf-001
uv run --no-sync homtech-evaluate --model artifacts/runs/six-class-rbf-001/best.joblib
```

Her eğitim ve değerlendirme çıktısı için boş bir klasör kullanılır.
`seven-linear` profilinde `--max-iter` varsayılanı 10.000'dir ve yakınsamama
uyarısı manifestte işaretlenir.
SVM karar skorları kalibre edilmiş duygu olasılıkları değildir; gelecekteki
güven eşiği ve kamera önerileri için ayrıca kalibrasyon/doğrulama gerekecek.

## Çıktılar ve izlenebilirlik

- `best.joblib`: HOG ayarları, sınıf sırası, eğitilmiş model hattı, seçilen C
  ve veri içerik fingerprint'leri.
- `validation_results.csv`: C, doğrulama accuracy/macro F1, yakınsama ve süre.
- `run_manifest.json`: Git durumu, sürümler, seed, veri üyelikleri, parametreler,
  aday sonuçları, en iyi adayın sınıf bazlı doğrulama ölçümleri ve koşunun durumu.
- `evaluation/metrics.json`: test accuracy, macro F1, sınıf bazlı ölçümler,
  kapsam dışı sınıflar, örnek sayıları ve model SHA-256.
- `evaluation/confusion_matrix.csv` ve `confusion_matrix.png`: satırlar gerçek,
  sütunlar tahmin sınıfları.

Joblib/pickle model dosyalarını yalnızca güvendiğiniz kaynaklardan yükleyin.
Farklı scikit-learn sürümlerinde model uyumluluğu garanti edilmez; kilit dosyası
ve manifestteki sürümleri koruyun.

## Testler

```powershell
uv run --no-sync python -m compileall -q src/homtech tests
uv run --no-sync python -m unittest discover -s tests -v
uv pip check
```

Testler sentetik şekillerle HOG'un kararlılığını, ölçekleme/veri ayrımını,
SVM seçimini, kaydetme/yüklemeyi, rapor üretimini ve değiştirilmiş test
verisinin reddedilmesini sınar. Sentetik sonuçlar gerçek yüz ifadesi başarısı
olarak raporlanmaz.

## Ürün hedefi

İlerleyen aşamalar kamera/yüz algılama, birkaç saniyelik kararlı tahmin,
PySide6 arayüzü, SQLite, kullanıcı onayı, manuel mod, ESP32/HTTP ile RGB kontrolü
ve Windows EXE. Kullanıcının beyanı ve tercihleri önceliklidir; yüz ifadesi kesin
bir ruh hâli ölçümü değildir. Kamera görüntüleri varsayılan olarak saklanmayacak.

RAF-DB erişimi, sağlayıcının verdiği koşullar kapsamında yürütülür.
Başvuru ve kaynak sayfası: [RAF-DB](http://www.whdeng.cn/RAF/model1.html).
