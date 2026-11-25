# Yerel proje arşivi

`classical-ml-transition-2026-11-17/`, HOG + SVM yöntemine geçilmeden önceki
PyTorch/MobileNetV3 kaynaklarını, testlerini, README'yi ve bağımlılık dosyalarını
korur. Aktif proje klasik makine öğrenmesi kullanır; bu eski hat çalıştırılmaz.

`legacy-2026-11-17/`, PyTorch + RAF-DB yapısına geçişten önceki çalışma alanını
korur. Aktif proje bu klasörden hiçbir modül veya veri yüklemez.

Arşiv içeriği:

- `src/`: TensorFlow eğitim hattı, HTTP backend, karar motoru, tarayıcı
  arayüzü, Caffe kaynakları ve geçiş öncesi PyTorch kaynaklarının kopyası.
- `tests/`: önceki backend, karar motoru ve eğitim testleri.
- `artifacts/`: eski `.keras` model, performans raporları ve geçici dosyalar.
- `data/`: FER2013, işlenmiş veri klasörü ve önceki deneme görselleri.
- `docs/`: önceki sistem mühendisliği belgeleri ve geliştirme rehberi.
- `scripts/`, `start_local.ps1`: önceki başlatma/ikon araçları.
- `reports/`: önceki çalışma logları.
- `tooling/`: eski yerel uv önbelleği ve kullanılmayan geçici sanal ortam.
- `README.previous.md`, `pyproject.toml`, `uv.lock`: önceki yapılandırma.
- `reorganization-manifest.json`: taşınan her dosya/klasörün eski ve yeni yolu.

RAF-DB indirmeleri `../data/downloads/rafdb/` altındadır. Klasör düzenlenirken
eski kaynaklar, modeller veya veri setleri silinmedi; yerel arşive taşındı.

Arşiv Git'e eklenmez; bu README izlenir. Eski çalışmayı incelemek için içerikleri
arşivden okuyun. Geri alma sırasında manifestteki yolları inceleyin ve aktif
dosyaların üzerine doğrudan yazmayın.
