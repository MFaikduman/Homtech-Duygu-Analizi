# HOMTECH EmotionAI

**Klasik makine öğrenmesiyle** yüz ifadesi sınıflandırma ve kullanıcı onayına
dayalı akıllı ev aydınlatma prototipi.

Aktif yöntem **HOG özellik çıkarımı + StandardScaler + PCA + RBF SVM**.
HOG, görüntünün yerel kenar ve gradyan yapısını sayısal özelliklere dönüştürür.
Varsayılan model kızgınlık, korku, mutluluk, üzüntü, şaşkınlık ve nötr
ifadelerini sınıflandırır.

## Yapı

- `src/homtech/ml/rafdb.py`: RAF-DB okuma, doğrulama ve veri ayrımı.
- `src/homtech/ml/features.py`: gri ton, boyutlandırma ve HOG çıkarımı.
- `src/homtech/ml/model.py`: ölçekleme + SVM ve model kaydetme/yükleme.
- `src/homtech/ml/train.py`: C değerlerini doğrulama kümesinde karşılaştırma.
- `src/homtech/ml/evaluate.py`: resmî test değerlendirmesi.
- `src/homtech/ml/metrics.py`: accuracy, macro F1 ve confusion matrix.
- `tests/`: veri, özellik çıkarımı ve eğitim/değerlendirme testleri.
- `data/downloads/`: özgün RAF-DB indirmeleri; Git dışında.
- `data/raw/rafdb/BasicEmo/`: hazırlanmış yüz görselleri ve etiketler; Git dışında.
- `artifacts/datasets/`: veri doğrulama raporları.
- `artifacts/runs/`: model, deney kayıtları ve değerlendirme sonuçları.
- `archive/`: önceki TensorFlow, Caffe ve PyTorch çalışmaları.

[Veri düzeni](data/README.md) · [Geliştirme rehberi](docs/emotionai.md) ·
[Arşiv](archive/README.md)

## Kurulum

Python 3.12 kullanın. Komutları proje kökünde çalıştırın:

```powershell
uv sync --locked
```

CUDA, PyTorch veya önceden eğitilmiş model indirmesi gerekmez. Eğitim CPU'da
çalışır. Önceki `--extra cuda`, `--extra training`, `--epochs` ve
`--device cuda` komutları bu yöntem için kullanılmaz.

## Veri kontrolü

```powershell
uv run --no-sync homtech-check-data --verify-images --output artifacts/datasets/rafdb-audit.json
```

Mevcut veri kontrolünde 15.339 görsel okunabilir; resmî eğitim kümesi 12.271,
test kümesi 3.068 görseldir. Doğrulama, resmî eğitim kümesinden sınıf bazında
ayrılır. Test kümesi hiperparametre seçiminde kullanılmaz.

## Eğitimi başlatma

```powershell
uv run --no-sync homtech-train --output-dir artifacts/runs/six-class-rbf-001
```

Varsayılan ayarlar 12 yönlü HOG, 128 PCA bileşeni ve RBF SVM için C=1'dir.
StandardScaler, PCA ve SVM yalnızca eğitim bölümünden öğrenir.
`--c-values` ile birden fazla aday verilirse doğrulama macro F1 skoru en yüksek
model kaydedilir. Yedi sınıflı doğrusal SVM için `--profile seven-linear` kullanılır.

Çıktılar: `best.joblib`, `validation_results.csv`, `run_manifest.json`.
Çıktı klasörü doluysa `six-class-rbf-002` gibi yeni bir ad kullanın.

## Nihai değerlendirme

```powershell
uv run --no-sync homtech-evaluate --model artifacts/runs/six-class-rbf-001/best.joblib
```

Altı sınıflı model, resmî test bölümündeki kapsam içi 2.908 görselde değerlendirilir.
Accuracy, macro F1, sınıf bazlı precision/recall/F1 ve confusion matrix
(JSON/CSV/PNG), koşunun `evaluation/` klasörüne yazılır. Test dosyalarının
içerik hash'leri eğitim manifestiyle eşleşmelidir. Joblib dosyalarını yalnızca
güvendiğiniz, kendi oluşturduğunuz koşulardan yükleyin.

`homtech-check-rafdb`, `homtech-train-rafdb` ve `homtech-evaluate-rafdb` aynı
araçlara yönlenen eşdeğer komut adlarıdır.

## İyileştirme deneyi

İlk tarama, resmî test sonucunu etkilemeden HOG ayarlarını ve doğrusal SVM'i
karşılaştırır:

```powershell
uv run --no-sync homtech-experiment --models linear --output-dir artifacts/runs/classical-search-001
```

Bu komut yedi sınıflı araştırma koşularında `baseline`, `orient12` ve `finegrid`
HOG ayarlarında C=0.003, 0.01 ve 0.03 değerlerini doğrulama macro F1 ile sıralar.

## Masaüstü arayüzü

Gri ve altın tonlarındaki Windows masaüstü uygulamasını başlatmak için:

```powershell
uv sync --locked
uv run --no-sync homtech-desktop
```

Üst çubuktaki **BİL4011 Sunumu**, final ödevinin yedi adımını yerel deney
raporlarından grafiklerle anlatır. **Analiz ve ön işleme** bölümünde yöntem
adımlarına tıklanabilir. **Model değerlendirmesi** bölümünde karışıklık
matrisi, test profili, satır yüzdesi, örnek sayısı ve sınıf metrikleri seçilebilir.
Bireysel hücreler seçilince o sınıfın örnek sayısı ve oranı açıklanır.
Bölümler ok tuşlarıyla ilerletilebilir.
**Tam ekran** ve **Uygulamaya geç** kontrolleri sınıf içi demo için kullanılabilir.

**Günlük**, **Sıcak ortam**, **Rahatlama** ve **Odak** kartları ışığı anında
önizler. **Modu uygula** seçilen modu etkinleştirir. **Vazgeç** etkin moda döner.
İfade analizinin önerisi de onaydan önce **Önizle** ile görülebilir.

**Hazır örnekler** kartları yedi ifadeden birini doğrudan modele gönderir.
Örnekler yerel RAF-DB `original.zip` arşivinden okunur.

Fotoğrafı önizleme alanına sürükleyip bırakın veya **Fotoğraf yükle** ile seçin.
**Kamerayı aç** ile canlı analizi
başlatın. Model yaklaşık saniyede iki kareyi denetler ve son tahmini gösterir.
Kamera ve çekilen kare önizlemede ayna gibi gösterilir. Model, kameranın
orijinal karesini analiz eder.
Işık önerisi için en az bir saniyeye yayılan üç ardışık güvenilir kare aynı ifadeyi
göstermelidir.
**Kareyi çek** seçeneği tek bir fotoğrafı analiz eder. Eşik altındaki tahminler
**Olası ifade** olarak gösterilir. İğrenme ve düşük skorlu tahminlerde
öneri çıkmaz. **Onayla ve uygula** ışık önizlemesini günceller.

Yakın kırpılmış fotoğraflar için ikinci bir yüz algılama denemesi yapılır.
**Yüzü seç** görünürse fotoğraf üzerinde sürükleyerek yüzün tamamını çerçeveleyin.
Yakın çekim ve el ile seçim sonuçları **Olası ifade** olarak gösterilir.

Uygulama `artifacts/runs/camera-rbf-001/best.joblib` dosyasını kullanır.
Yeni kurulumda RAF-DB'nin orijinal görsel arşiviyle modeli oluşturmak için
`uv run --no-sync homtech-train --profile camera-rbf` çalıştırın.
Yakın çekimler için hizalı fotoğraf modelini de hazırlamak üzere
`uv run --no-sync homtech-train --profile seven-rbf` çalıştırılabilir.

## Testler

```powershell
uv run --no-sync python -m compileall -q src/homtech tests
uv run --no-sync python -m unittest discover -s tests -v
uv pip check
```

Otomatik testler küçük sentetik görseller kullanır. RAF-DB model sonuçları
eğitim koşusunun `evaluation/` klasöründedir.

## Sonraki aşamalar

SQLite tercihleri, kullanıcı onayıyla ESP32/HTTP aydınlatma kontrolü ve EXE.
Modelin çıktısı görüntüdeki yüz ifadesine dair bir tahmindir.
