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
5. [x] GitHub otomatik test/yayın akışına yeni paketleri ekle; 0.3.0 olarak yayımla.
6. [x] Releases indirmelerini, sağlama toplamlarını ve paket içeriğini uzaktan doğrula.

Son adlandırma kararı: Ana uygulama Uzeyir Control; teşhis modülü Uzeyir Doctor. Paket ve başlatıcı adı uzeyir-control; eski komut, masaüstü kimliği ve kullanıcı ayarları uyumluluk için korunur.

## 0.3.1 — ortak kaynak arşiviyle yayın düzeltmesi

1. [x] Fedora ve Arch kaynak içeriklerinin aynı, gzip akışlarının farklı olduğunu doğrula.
2. [x] Kaynağı bir kez üret; her derlemede içerik/izin kontrolüyle aynı arşivi kullan.
3. [x] Beş dağıtım ve tam yayın toplama işlemini tekrar doğrula.
4. [x] 0.3.1 paketlerini yayımla; indirmeleri ve kullanıcı kurulumunu doğrula.

## 0.4.0 — kesintisiz geçişler ve kullanıcı deneyimi

16 Ekim 2026: Kullanıcı hata düzeltmelerini, animasyon kalitesini ve bütün sayfalarda
çok akıcı geçişleri önceliklendirdi. Geliştirme ayrı kopyada sürer; aynı davranışlar
bağımsız Uzeyir Doctor'a da taşınır.

1. [x] Geçişleri, yinelenen animasyonları ve mevcut test/yayın altyapısını incele.
2. [x] Tam sayfa kaydırma yerine kısa mesafeli, kesilince devamlılığını koruyan ortak geçiş ekle.
3. [x] Sol menü göstergesini, kart ritmini ve işlem geri bildirimlerini iyileştir.
4. [x] Hızlı gezinme, pencere boyutu, klavye, dil ve hareket azaltma regresyonlarını doğrula.
5. [x] İyileştirmeleri bağımsız Doctor'a taşı; iki uygulamanın görünümünü ve hareketini kontrol et.
6. [x] Sürümleri ve notları güncelle; dağıtım paketlerini üret ve GitHub CI'da doğrula.
7. [x] İki sürümü yayımla; indirmeleri ve sağlama toplamlarını uzaktan doğrula.

17 Ekim 2026 ek isteği: Daha fazla animasyon; uygulama düzeni, GitHub tanıtımı
ve detaylı sürüm yayını. Kullanıcı uzakta; rutin kararlar sorulmadan uygulanır.

- [x] Temsili verilerle güncel ekran görüntüsü ve hareketli önizleme hazırla.
- [x] İki README'yi, indirme bağlantılarını ve sürüm/kurulum belgelerini yenile.
- [x] Kaynağı ve paketleri yayımla, GitHub sayfalarını ve indirmeleri doğrula.

## Uygulama içinden güncelleme — yayın öncesi ek kapsam

17 Ekim 2026: GitHub Releases'ta yayımlanan sürümler uygulamadan bulunup
kurulabilsin. Kullanıcı soru sorulmadan planı genişleterek tamamlamayı istedi.

1. [x] Mevcut sürümle uzak sürümü karşılaştır; yalnız doğru uygulama/depo ve uygun paketi seç.
2. [x] Güncelleme penceresine sürüm notları, isteğe bağlı açılış kontrolü ve yeni sürüm bildirimi ekle.
3. [x] Paketi arka planda gerçek ilerleme, iptal ve yeniden deneme ile indir.
4. [x] Boyutu, GitHub SHA-256 özetini ve SHA256SUMS dosyasını doğrulamadan kurulum açma.
5. [x] Mevcut PackageKit hizmetiyle kullanıcı tarafından başlatılan kurulumu uygulamada izle;
   hizmet yoksa dağıtımın paket kurucusuna açık geri bildirimle geç.
6. [x] Kurulu sürümü doğrula; yalnız başarılı kurulumda yeniden başlatmayı teklif et.
   Hata veya iptalde çalışan sürümü ve kullanıcı tercihlerini koru.
7. [x] Ağ hatası, bozuk paket, eski/yanlış sürüm, hızlı tekrar, iptal ve pencere kapanışını test et.
8. [x] Güncelleme akışını iki uygulamaya taşı; belgeleri, paketleri ve yayın doğrulamasını yenile.

## 0.4.0 yayını tamamlandı — 18 Ekim 2026

[Uzeyir Control 0.4.0](https://github.com/Tubix777/linux-control/releases/tag/v0.4.0)
ve [Uzeyir Doctor 0.2.0](https://github.com/Tubix777/uzeyir-doctor/releases/tag/v0.2.0)
yayımlandı. İki uygulamanın ana dal ve etiket yayın işleri beş dağıtımda başarılı.
Control 257, Doctor 111 test içeriyor; Fedora/Arch yalnız dpkg-deb araç testini atlıyor.

Her sürümün yedi dosyası halka açık bağlantılardan yeniden indirildi. Boyutlar,
GitHub SHA-256 özetleri ve SHA256SUMS eşleşiyor. Control kaynak arşivindeki 133,
Doctor arşivindeki 81 dosya etiketlenen kaynakla birebir aynı. Arch derleme tarifi
ve kaynak RPM aynı kanonik arşivi içeriyor. Canlı güncelleyici eski sürüm numarasıyla
DEB/RPM/Arch paketlerini seçip indirerek yeniden doğruladı. Gerçek sistem
yetkilendirmesi bu testlerde uygulanmadı.

[Makine tarafından okunabilir yayın doğrulaması](docs/release-verification.json)
etiketlenen sürümü kaydeder; bu planın tamamlanma kaydı sürüm etiketinden sonra eklenmiştir.

## 0.5.0 — Graphite / Inter, premium kullanım deneyimi

24 Ekim 2026: Kullanıcı Graphite yönünü seçti; daha özenli ve premium bir
uygulama istedi. Siyah/gri/beyaz palet, indirme sayfaları, dil seçimi, gerçek
veri ve güncelleyici korunur. Geliştirme ayrı dalda yapılır.

1. [x] Inter fontunu lisansı ve sabit kaynak kaydıyla uygulamaya dahil et.
2. [x] Okunaklı yazı ölçeği, sakin başlıklar, ortak boşluk ve kontrol ölçüleri uygula.
3. [x] Sol menü, sayfalar, sonuçlar, indirmeler ve güncelleme penceresini birlikte düzenle.
4. [x] Geçişleri ve gerçek işlem geri bildirimlerini ortak ritme getir; hareket azaltmayı koru.
5. [x] Türkçe/İngilizce, dar/geniş pencere, klavye ve mevcut davranış testlerini doğrula.
6. [x] Gerçek GTK arayüzünden kişisel veri içermeyen güncel görüntüler ve hareketli önizleme hazırla.
7. [ ] Sürüm, belgeler ve dağıtım paketlerini yenile; kaynakları ve sürümü GitHub'da yayımla.
8. [ ] Herkese açık paketleri, kaynak tutarlılığını ve güncelleyici indirmelerini doğrula.
