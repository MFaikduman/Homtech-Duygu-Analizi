# Veri klasörleri

```text
data/
├── downloads/rafdb/
│   ├── basic/                Sağlayıcıdan indirilen özgün klasör
│   │   ├── Annotation/       Ek anotasyon arşivleri
│   │   ├── EmoLabel/         Resmî ifade etiketleri
│   │   ├── Feature/          Sağlayıcının hazır özellikleri
│   │   ├── Image/            aligned.zip ve original.zip
│   │   └── README.txt
│   └── loose-files/          Köke ayrı eklenmiş dosyalar, adları korunarak
└── raw/rafdb/BasicEmo/
    ├── EmoLabel/list_patition_label.txt
    └── Image/aligned/        Açılmış hizalanmış yüz görselleri
```

`downloads/` kaynak indirmeleri saklar. Eğitim yalnızca `raw/` altındaki açık
görselleri ve etiketleri kullanır. Her iki klasörün içeriği Git dışında tutulur.

Köke ayrı eklenmiş bazı dosyaların uzantıları içerikleriyle uyuşmuyordu;
örneğin `aligned (1).zip` bir MATLAB dosyasıydı. Bunlar `loose-files/` içinde
değiştirilmeden korunur. Eğitim verisi, düzeni doğru olan `basic/` klasöründeki
`Image/aligned.zip` ve `EmoLabel/list_patition_label.txt` dosyalarından hazırlanır.

Eski FER2013 ve deneme görselleri `../archive/legacy-2026-11-17/data/` altına
taşındı. Veri doğrulama raporu `../artifacts/datasets/rafdb-audit.json` dosyasına
yazılır.
