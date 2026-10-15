# Uzeyir Control — uygulama ve yayın planı

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
9. [x] GitHub deposunu oluştur, kaynakları ve ilk ön sürümü yayımla; uzaktan doğrula.

## 0.2.0 — tasarım ve indirme sayfaları

14 Ekim 2026 isteği: Yazı tipleri ve sayfa tasarımı yeniden ele alınacak;
her modülün sol menüden açılan kendi indirme sayfası olacak. Kullanıcı iki saat
uzakta; rutin kararları sorulmadan, akıcılık ve kalite önceliğiyle tamamlanacak.
Ortak çalışma klasörü korunuyor; geliştirme ayrı klon ve dalda yapılıyor.

1. [x] Güncel ana dalı ve önceki değişiklikleri incele; ayrı çalışma kopyasını hazırla.
2. [x] Resmî Anvil/Wheel/Linux Control sürüm ve paket bağlantılarını doğrula.
3. [x] Lisanslı yerel Manrope yazı tipiyle ortak tipografi, sol menü ve kart düzenini yenile.
4. [x] Üç modüle ayrı indirme, paket seçimi, kurulum komutu ve sürüm sayfaları ekle.
5. [x] Donanım, direksiyon ve teşhis ekranlarını ortak bilgi hiyerarşisine uyarla.
6. [x] Dil, klavye, kaydedilmemiş seçimler, çevrimdışı kullanım ve hareket azaltmayı doğrula.
7. [x] Sanal Wayland oturumunda davranış testlerini ve farklı pencere boyutlarını doğrula.
8. [x] Gerçek arayüz görüntülerini kontrol et; RPM, kaynak ve checksum dosyalarını üret.
9. [x] Uzak ana dalda yeni çalışma varsa koruyarak yayımla; GitHub test/yayın sonucunu doğrula.

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

- 0.2.0: 200 test özel KWin/Wayland oturumunda geçti; altı görünümün küçük/geniş yerleşimi doğrulandı.
- 0.2.0: Fedora noarch/kaynak RPM üretildi; font, CSS, indirme kayıtları ve OFL lisansı pakette doğrulandı.

## 0.2.1 — hareket ve akıcılık

15 Ekim 2026: Daha fazla animasyon isteği. Ortak kaynak klasörüne dokunmadan
ayrı geliştirme dalında, canlı ölçüm ve direksiyon girişini geciktirmeden ilerle.

1. [x] Güncel ana dalı doğrula; sayfa, indirme ve tarama animasyonlarını incele.
2. [x] Yönlü bölüm/indirme geçişleri ve sol menü seçim vurgusu ekle.
3. [x] Başlıkları, indirme satırlarını ve komutları sabit yerleşimde kademeli hareketle göster.
4. [x] Gerçek tarama sırasında hareketli sinyal; bitişte kısa hale ve sonuçlara yükselerek giriş ekle.
5. [x] Gizlenme, kapatma, hareket azaltma ve dinamik liste yaşam döngüsünü test et.
6. [x] Yerel arayüzü küçük/geniş pencerede kontrol et; animasyonu kaydet ve RPM üret.
7. [x] Sürümü artır; kaynağı ve paketleri GitHub'da yayımla, doğrula ve uygulamayı aç.

## 0.3.0 — Uzeyir Control ve Linux dağıtım paketleri

15 Ekim 2026: Ubuntu, Deepin, Zorin ve Arch için GitHub Releases üzerinden
indirilebilir kurulum seçenekleri ekle. Ortak çalışma klasörünü koru.

1. [x] Mevcut kaynak ve paketleri, dağıtım tabanlarını ve asgari bağımlılıkları incele.
2. [x] DEB ve Arch paketlerini güvenli ortak içerikle üret; lisans ve masaüstü girişini koru.
3. [x] İndirme arayüzünü ve Türkçe/İngilizce kurulum yönergelerini güncelle.
4. [x] Yalıtılmış Ubuntu/Deepin/Arch ortamlarında kurulum ve yerel arayüzü doğrula.
5. [ ] GitHub otomatik test/yayın akışına yeni paketleri ekle; 0.3.0 olarak yayımla.
6. [ ] Releases indirmelerini, sağlama toplamlarını ve paket içeriğini uzaktan doğrula.

Son adlandırma kararı: Ana uygulama Uzeyir Control; teşhis modülü Uzeyir Doctor. Paket ve başlatıcı adı uzeyir-control; eski komut, masaüstü kimliği ve kullanıcı ayarları uyumluluk için korunur.
