# Bu Projeyi Nasil Yaptik?

Bu projede amacimiz, bir insanin yuz ifadesine bakip duygusunu tahmin etmek ve bu sonuca gore HOMTECH icin uygun bir akilli ev modu onermekti.

Kisaca soyle ilerledik:

## 1. Veri Setini Hazirladik

Ilk olarak FER-2013 isimli duygu veri setini kullandik. Bu veri setinde farkli insan yuzleri var ve her gorsel bir duygu etiketi ile geliyor.

Kullandigimiz duygular:

- angry
- disgust
- fear
- happy
- sad
- surprise
- neutral

Bu verileri `data/raw/fer2013/train` ve `data/raw/fer2013/test` klasorlerine yerlestirdik.

## 2. Goruntuleri Modele Uygun Hale Getirdik

Modelin duzenli calisabilmesi icin tum gorselleri ayni formata getirdik.

Bu asamada:

- gorselleri `48x48` boyutunda kullandik
- veriyi TensorFlow ile klasorlerden okuttuk
- egitim sirasinda veri artirma yontemlerinden yararlandik

Boylece model, farkli yuz ifadelerini daha iyi ogrenebilecek bir yapıya kavustu.

## 3. Modeli Kurduk ve Egitdik

Projede TensorFlow ve Keras kullandik. Egitim kisminda derin ogrenme tabanli bir goruntu siniflandirma modeli kurduk.

Sistem genel olarak sunu yapti:

- egitim verisini yukledi
- modeli kurdu
- modeli duygu siniflarini ogrenmesi icin egitti
- en iyi sonucu veren agirliklari kaydetti

Egitim sonunda model dosyasi `artifacts/emotion_cnn.keras` icine kaydedildi.

## 4. Modeli Test Ettik

Modeli egittikten sonra test verisi uzerinde denedik. Burada amacimiz, modelin daha once gormedigi gorsellerde ne kadar basarili oldugunu olcmekti.

Bu asamada:

- accuracy
- precision
- recall
- f1-score
- confusion matrix

gibi degerlere baktik.

Yani sadece "dogru mu yanlis mi" diye degil, hangi duygularda daha iyi ya da daha zayif oldugunu da inceledik.

## 5. Tahmin Sonucunu Akilli Ev Onerisine Cevirdik

Bu projenin en onemli yani sadece duygu tahmini yapmasi degil, bu tahmini bir akilli ev senaryosuna donusturmesidir.

Ornek olarak:

- mutluysa daha enerjik bir ortam
- uzgunse daha rahatlatıcı bir ortam
- notrse daha odaklanmaya uygun bir ortam

oneriyoruz.

Bu kisimda aydinlatma, muzik, sicaklik, perde ve bildirim duzeni gibi ayarlar icin basit bir karar yapisi kurduk.

## 6. Tek Gorselle Tahmin Ozelligi Ekledik

Sonra egitilen modeli kullanip tek bir fotograf uzerinden tahmin yapabilen bir yapi ekledik.

Bu bolumde sistem:

- resmi aliyor
- mumkunse yuz bolgesini buluyor
- duygu tahmini yapiyor
- guven skorunu veriyor
- buna uygun HOMTECH modunu olusturuyor

Boylece proje sadece egitim yapan bir calisma olmaktan cikti, gercek kullanim hissi veren bir hale geldi.

## 7. Web Arayuzu Hazirladik

Projeyi daha rahat gosterebilmek icin bir web arayuzu de ekledik.

Bu arayuzde iki temel kullanim var:

- senaryo modu
- gorsel analizi modu

Senaryo modunda duygu ve ortam bilgilerini elle secip sonucu gosterebiliyoruz.
Gorsel analizi modunda ise bir fotograf yukleyip modelin tahminini ekranda gorebiliyoruz.

Bu sayede proje sunumda daha anlasilir ve daha gorsel bir hale geldi.

## 8. Sonuc Olarak Ne Yaptik?

Kisaca bu projede:

1. duygu veri setini hazirladik
2. goruntuleri isledik
3. bir duygu tanima modeli egittik
4. modeli test ettik
5. tahmini akilli ev moduna cevirdik
6. bunu hem terminalde hem web arayuzunde gosterilebilir hale getirdik

Yani bu proje, yuz ifadesinden duygu anlayan ve buna gore ortam onerisi sunan basit ama calisan bir yapay zeka prototipi olarak gelistirildi.
