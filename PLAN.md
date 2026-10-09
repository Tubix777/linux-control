# Linux Control — uygulama ve yayın planı

Kullanıcının kararları: Üç uygulama tek pencerede birleşecek. Soldaki büyük
düğmeler Donanım, Direksiyon ve Sorun Teşhisi bölümlerini açacak. Siyah zemin,
gri tonları, beyaz yazılar, akıcı geçişler ve tarama sonrası animasyonlu otomatik
kaydırma korunacak. Türkçe ve İngilizce ortak dil seçimi olacak. Tamamlanınca
GitHub hesabında yayımlanacak; rutin uygulama kararları için tekrar soru sorulmayacak.

## Tamamlama sırası

1. [x] Mevcut üç uygulamayı incele; ayrı çalışma kopyasını ve lisansları hazırla.
2. [x] Ortak yerel GTK4/libadwaita penceresini, sol menüyü ve kalıcı tercihleri tamamla.
3. [x] Anvil ölçümlerini ve sınırlandırılmış açık kontrollerini Donanım bölümüne taşı.
4. [x] Wheel cihaz algılama, canlı giriş ve profillerini Direksiyon bölümüne taşı.
5. [x] Doctor taraması, SSD yüzdesi ve sonuç animasyonunu Sorun Teşhisi bölümüne taşı.
6. [x] Türkçe–İngilizce geçişini, hareket azaltmayı ve pencere boyutlarını doğrula.
7. [x] Donanım yazma sınırları, yaşam döngüsü ve arayüz davranışlarını test et.
8. [x] Gerçek yerel verilerle arayüzü aç, görsel kontrol yap; RPM ve kaynak paketini üret.
9. [ ] GitHub deposunu oluştur, kaynakları ve ilk ön sürümü yayımla; uzaktan doğrula.

## Kalite ölçütleri

- Hiçbir bölüm başka bir uygulama penceresi açarak birleştirilmiş sayılmaz.
- Ölçüm ve cihaz sorguları arayüz iş parçacığını bekletmez.
- Sekme değişimi, profil yükleme ve dil değişimi donanıma yazmaz.
- Bilinmeyen veya eski sağlık verisi sayısal sağlık yüzdesi gibi sunulmaz.
- SSD yüzdesi tahmini kalan dayanıklılık/ömür olarak açıkça adlandırılır.
- Kullanıcı elle kaydırırsa otomatik kaydırma durur; hareket azaltma tercihine uyulur.
- Ayrıcalıklı fan işlemleri yalnız mevcut doğrulanmış yardımcı ve kart/kanal sınırlarıyla yapılır.
- Eski uygulamalar ve depolar korunur; yeni uygulama bağımsız depoda yayımlanır.
- Yayına kişisel günlükler, cihaz seri numaraları veya kimlik bilgileri eklenmez.
- Gerçek cihazla doğrulanmayan özellikler sürüm notlarında açıkça belirtilir.

## Sonuç kayıtları

Test sonuçları, görsel kontrol ve yayın bağlantıları tamamlandıkça burada kaydedilir.

- İlk birleşik kontrol: özel sanal Wayland oturumunda 155 test geçti.
- Arka plan direksiyon işlemleri ve yaşam döngüsü iyileştirmeleri sonrası 165 test geçti.
- Üç sayfa gerçek yerel okuma ve ayrıca açıkça işaretlenmiş direksiyon demosuyla çizdirildi.
- Görsel kontrolde bulunan sol menü genişliği ve eksik tema ikonları düzeltildi.
- Son birleşik doğrulamada 173 test geçti; görsel ve davranış testleri atlanmadı.
- Fedora 44 için noarch RPM, kaynak RPM ve kaynak arşivi başarıyla üretildi.
