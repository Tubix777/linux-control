# Uzeyir Control 0.4.0 — akıcı geçişler ve uygulama içinden güncelleme

Bölüm ve indirme sayfaları artık bütün pencereyi kaydırmak yerine 360 ms içinde
kısa mesafeyle hareket ederek karışır. Hızlı gezinmede geçiş son çizilen kareden
başlar; sayfa değerleri ve etkin bölüm aynı anda güncellenir. Sol menüdeki tek
seçim göstergesi hedef düğmeye kayar.

## Uygulama içinden güncelleme

Üst çubuk veya Ctrl+U yeni güncelleme penceresini açar. GitHub'daki kararlı sürüm
sistem paketine göre seçilir; notlar gösterilir. İndirme gerçek byte ilerlemesi,
iptal ve yeniden deneme sunar. Boyut, API SHA-256 ve SHA256SUMS doğrulanır;
kurulumdan hemen önce dosya yeniden kontrol edilir.

Kullanıcı başlattığında mevcut PackageKit hizmeti ve normal sistem yetkilendirmesi
kullanılır. Hizmet yoksa yerel paket kurucusu/komut akışına geçilir. Kurulu sürüm
sorgulanmadan başarı gösterilmez. Açılış kontrolü isteğe bağlı ve başlangıçta kapalıdır.
Yeni ayrıcalıklı yardımcı veya geniş cihaz izni kurulmaz. İlk güncelleyici sürümünü
kurduktan sonra sonraki sürümler uygulamadan alınabilir.


## Deneyim ve düzeltmeler

- Yeni sayfanın üstüne ikinci bir kart solması bindirilmez. Kart girişleri daha
  kısa ve okunaklıdır; iç içe kartlar birbirini tekrar soluklaştırmaz.
- Geçişin ilk karesinde kararmaya yol açan çizim yakalama durumu düzeltildi.
  İlk geçiş ve yarıda yönlendirme aynı görüntüyü koruyan piksel testleriyle denetlenir.
- Giriş alanlarının tıklama konumu hareketi takip eder. Hızlı seçimler son hedefi
  açar; kaydedilmemiş direksiyon/profil değerleri korunur.
- Tarama düğmesi işlem durumunu gösterir. Gerçek tamamlanmada kısa bir vurgu
  oynar; başarısız tarama tamamlanan bir kontrol olarak sayılmaz.
- Açık kanıt/çözüm ayrıntıları dil ve filtre değişiminde korunur.
- Komut kopyalama düğmesinde kısa bir onay görünür. Liste yenilenince eski
  onay zamanlayıcıları bırakılır; klavye odağı karşılık gelen eylemde kalır.
- Uzeyir Doctor indirme ekranı artık bağımsız Doctor deposuna ve paketlerine gider.
- Küçültme, gizleme, kapatma veya hareket azaltma devam eden hareketi sonlandırır.
  Canlı giriş değerleri geciktirilmez.

- Ubuntu 24.04 ve Deepin 25 üzerindeki eski libadwaita ile açılış anında
  kapatılan güncelleme penceresinin yeniden açılması düzeltildi.
- GitHub tanıtımı gerçek arayüz önizlemeleri, sık sorulan sorular, katkı rehberi
  ve hata/özellik bildirim şablonlarıyla yenilendi.

## Paketler

| Sistem | Dosya |
| --- | --- |
| Ubuntu 24.04 / 26.04, Deepin 25, Zorin 18, Debian 13 | `uzeyir-control_0.4.0-1_all.deb` |
| Fedora 44 | `uzeyir-control-0.4.0-1.fc44.noarch.rpm` |
| Güncel Arch | `uzeyir-control-0.4.0-1-any.pkg.tar.zst` |
| Arch çevrimdışı derleme | `uzeyir-control-0.4.0-arch-build.tar.gz` |
| Kaynak / kaynak RPM | `uzeyir-control-0.4.0.tar.gz`, `uzeyir-control-0.4.0-1.fc44.src.rpm` |

`SHA256SUMS` paketleri ve kaynak arşivlerini kapsar. Bütün dağıtımlar tek kanonik
kaynak arşivini kullanır. Python ≥ 3.11, GTK ≥ 4.12 ve libadwaita ≥ 1.5 gerekir.
Fedora, Ubuntu 24/26, Deepin ve Arch işlerinde test, kurulum ve kurulu altı görünüm
kontrol edilir. Zorin desteği Ubuntu tabanını kullanır; fiziksel direksiyon ve fan
uyumluluğu README'deki donanım desteğiyle sınırlıdır.

## English

Short frame-clock transitions retain the last painted frame when interrupted.
A sliding sidebar indicator, calmer card entrances, real-operation completion
feedback and copy confirmations make navigation more responsive. Expanded
findings, unsaved values and keyboard focus survive rebuilds. Failed scans no
longer count as successful checks. The Doctor download page now points to the
standalone Uzeyir Doctor repository. Reduced motion, resize, hide and close
settle transitions immediately. Device-control behavior is unchanged. The in-app updater verifies GitHub release packages and uses normal system package authorization only when requested.

---

# Uzeyir Control 0.3.1 — Linux kurulum paketleri ve ortak kaynak arşivi

Yayın düzeltmesi: Fedora ve Arch artık bir kez üretilen aynı kaynak arşivini
çevrimdışı kullanır. İçerik ve dosya izinleri paketlemeden önce doğrulanır.
Farklı sıkıştırma kütüphanelerinden kaynaklanan checksum farkı giderildi.

Uygulamanın yeni adı **Uzeyir Control**. Donanım, Direksiyon ve Sorun Teşhisi
aynı pencerede kalır; teşhis modülünün adı **Uzeyir Doctor** olur.
Siyah/gri/beyaz görünüm ve animasyonlar korunur.
Mevcut dil/hareket tercihleri, Wheel profilleri ve masaüstü kimliği korunur.
Eski `linux-control` komutu da uyumluluk için çalışmaya devam eder.

| Dağıtım | Releases dosyası |
| --- | --- |
| Ubuntu 24.04 / 26.04, Zorin 18, Deepin 25, Debian 13 | `uzeyir-control_0.3.1-1_all.deb` |
| Güncel Arch Linux | `uzeyir-control-0.3.1-1-any.pkg.tar.zst` |
| Arch kaynak tarifi | `uzeyir-control-0.3.1-arch-build.tar.gz` (PKGBUILD, kaynak ve sabit SHA-256) |
| Fedora 44 | `uzeyir-control-0.3.1-1.fc44.noarch.rpm` |
| Kaynaktan çalıştırma / yeniden derleme | `uzeyir-control-0.3.1.tar.gz` ve `.src.rpm` |

[Dağıtıma göre kurulum ve kaldırma](https://github.com/Tubix777/linux-control/blob/v0.3.1/docs/install.md)

DEB: `sudo apt install ./uzeyir-control_0.3.1-1_all.deb`.
Arch için önce sistemi ve bağımlılıkları güncelleyin, ardından `sudo pacman -U ./uzeyir-control-0.3.1-1-any.pkg.tar.zst`.
Fedora: `sudo dnf install ./uzeyir-control-0.3.1-1.fc44.noarch.rpm`.
Kurulumdan sonra menüden **Uzeyir Control**'ü açın. Uygulamayı sudo ile çalıştırmayın.

Asgari Python 3.11, GTK 4.12 ve libadwaita 1.5 gerekir. Ubuntu 22.04,
Zorin 17 ve Deepin 23 hedeflenmemiştir. Bunlar projenin GitHub paketleridir;
AUR veya bir uygulama mağazasında yayımlandığı iddia edilmez.

Kurulumlar Ubuntu 24.04/26.04, Deepin 25, Fedora 44 ve güncel Arch konteynerlerinde
kontrol edilir. Her ortamda özel Wayland oturumunda arayüz testleri ve kurulu
paketin altı görünümü açılır; gerçek Zorin masaüstü ve fiziksel donanım testi
yapıldığı iddia edilmez. Ubuntu/Deepin'de 216 test; Fedora/Arch'ta DEB oluşturma
araç testi dışında aynı testler çalışır. DEB simge yükleyicisi bağımlılığı ve
yeni libadwaita için direksiyon anahtarlarının yerleşimi düzeltilmiştir.

SHA256SUMS bütün kurulum ve kaynak dosyalarını kapsar. Yeni paketler yönetici
hizmeti, geniş cihaz izni veya yeni fan yardımcısı kurmaz.

## English

Linux Control is now **Uzeyir Control**, preserving preferences, profiles and
its desktop identity. Releases include a DEB for compatible Ubuntu/Zorin/Deepin/
Debian systems, an Arch pacman package plus an offline pinned PKGBUILD/source
bundle, and Fedora binary/source RPMs. Dependencies remain Python ≥ 3.11,
GTK ≥ 4.12 and libadwaita ≥ 1.5. Five isolated distro environments validate
installation, native UI tests and all six installed views. Zorin's Ubuntu base
is covered; this is not a claim of full Zorin desktop or physical-device testing.

---

# Uzeyir Control 0.3.0 — Yeni ad ve Linux kurulum paketleri

Uygulamanın yeni adı **Uzeyir Control**. Donanım, Direksiyon ve Sorun Teşhisi
aynı pencerede kalır; teşhis modülünün adı **Uzeyir Doctor** olur.
Siyah/gri/beyaz görünüm ve animasyonlar korunur.
Mevcut dil/hareket tercihleri, Wheel profilleri ve masaüstü kimliği korunur.
Eski `linux-control` komutu da uyumluluk için çalışmaya devam eder.

| Dağıtım | Releases dosyası |
| --- | --- |
| Ubuntu 24.04 / 26.04, Zorin 18, Deepin 25, Debian 13 | `uzeyir-control_0.3.0-1_all.deb` |
| Güncel Arch Linux | `uzeyir-control-0.3.0-1-any.pkg.tar.zst` |
| Arch kaynak tarifi | `uzeyir-control-0.3.0-arch-build.tar.gz` (PKGBUILD, kaynak ve sabit SHA-256) |
| Fedora 44 | `uzeyir-control-0.3.0-1.fc44.noarch.rpm` |
| Kaynaktan çalıştırma / yeniden derleme | `uzeyir-control-0.3.0.tar.gz` ve `.src.rpm` |

[Dağıtıma göre kurulum ve kaldırma](https://github.com/Tubix777/linux-control/blob/v0.3.0/docs/install.md)

DEB: `sudo apt install ./uzeyir-control_0.3.0-1_all.deb`.
Arch için önce sistemi ve bağımlılıkları güncelleyin, ardından `sudo pacman -U ./uzeyir-control-0.3.0-1-any.pkg.tar.zst`.
Fedora: `sudo dnf install ./uzeyir-control-0.3.0-1.fc44.noarch.rpm`.
Kurulumdan sonra menüden **Uzeyir Control**'ü açın. Uygulamayı sudo ile çalıştırmayın.

Asgari Python 3.11, GTK 4.12 ve libadwaita 1.5 gerekir. Ubuntu 22.04,
Zorin 17 ve Deepin 23 hedeflenmemiştir. Bunlar projenin GitHub paketleridir;
AUR veya bir uygulama mağazasında yayımlandığı iddia edilmez.

Kurulumlar Ubuntu 24.04/26.04, Deepin 25, Fedora 44 ve güncel Arch konteynerlerinde
kontrol edilir. Her ortamda özel Wayland oturumunda arayüz testleri ve kurulu
paketin altı görünümü açılır; gerçek Zorin masaüstü ve fiziksel donanım testi
yapıldığı iddia edilmez. Ubuntu/Deepin'de 215 test; Fedora/Arch'ta DEB oluşturma
araç testi dışında aynı testler çalışır. DEB simge yükleyicisi bağımlılığı ve
yeni libadwaita için direksiyon anahtarlarının yerleşimi düzeltilmiştir.

SHA256SUMS bütün kurulum ve kaynak dosyalarını kapsar. Yeni paketler yönetici
hizmeti, geniş cihaz izni veya yeni fan yardımcısı kurmaz.

## English

Linux Control is now **Uzeyir Control**, preserving preferences, profiles and
its desktop identity. Releases include a DEB for compatible Ubuntu/Zorin/Deepin/
Debian systems, an Arch pacman package plus an offline pinned PKGBUILD/source
bundle, and Fedora binary/source RPMs. Dependencies remain Python ≥ 3.11,
GTK ≥ 4.12 and libadwaita ≥ 1.5. Five isolated distro environments validate
installation, native UI tests and all six installed views. Zorin's Ubuntu base
is covered; this is not a claim of full Zorin desktop or physical-device testing.

---

# Linux Control 0.2.1 — Daha akıcı hareketler

- Bölümler arasında yukarı/aşağı, indirme sayfasına giderken ve dönerken sağ/sol geçiş.
- Sol menüde kısa seçim vurgusu ve indirme simgesinde fare tepkisi.
- Başlıklar ve donanım kartlarının içeriğinde yerleşimi değiştirmeyen kademeli yükselme/belirme.
- Paket biçimi değişince indirme satırları ve kurulum komutlarında yeniden giriş animasyonu.
- Gerçek tarama sırasında dönen teşhis sinyali ve tamamlanınca tek seferlik kısa halka.
- Sonuç içeriklerinde yükselerek belirme; mevcut yumuşak otomatik kaydırma ve elle kesme korunur.
- Gizlenme, kapanma, hareket azaltma ve masaüstü tercihi değişiminde animasyonlar durur.
- Yenilenen paket listeleri eski animasyon bağlantılarını bırakır; gizli yenileme göstergeleri durur.

Canlı direksiyon/pedal değerleri geciktirilmez. Etkinlik sinyali bir yüzde veya
sağlık ölçümü değildir. Sistem taraması yerel ve salt okunur; yeni donanım yazımı
eklenmedi. Türkçe/İngilizce, çevrimdışı indirme bilgileri ve kaydedilmemiş değerler korunur.

208 test özel Fedora 44/GTK/Wayland oturumunda geçti; arayüz testleri atlanmadı.
Altı görünüm küçük/geniş pencerede ve gerçek salt okunur sistem taramasıyla kontrol edildi.
Fiziksel direksiyon kuvvet geri bildirimi veya fan yazımı bu sürümde denenmedi.

Fedora noarch RPM, kaynak RPM, kaynak arşivi ve SHA-256 sağlama toplamları sunulur.

## English

Directional navigation, a short sidebar selection accent, staggered paint-only
header/hardware entrances and animated package-format changes make the native
UI more fluid. Diagnostics add a real-operation activity sweep, a finite
completion halo and lifted result content. Hidden or replaced views release
their callbacks; both reduced-motion preferences are respected. Wheel input
remains immediate and no hardware-write behavior changes. The isolated GTK
suite passes 208 tests with no GUI skips; physical force feedback was not tested.

---

# Linux Control 0.2.0 — Yeni tasarım ve indirme sayfaları

Donanım, Direksiyon ve Sorun Teşhisi ekranları ortak Manrope yazı tipi, sade sol
menü, daha belirgin başlıklar ve siyah/gri/beyaz kartlarla yeniden düzenlendi.
Her bölümün sol menüde kendi indirme sayfası bulunuyor.

- Resmî Anvil ve Wheel sürümleri için mevcut RPM, DEB, taşınabilir ve kaynak
  paketleri; Fedora Doctor için birleşik Linux Control paketi.
- Paket seçimi, tarayıcıda açılan indirme bağlantıları, sürüm/kaynak/sorun
  bağlantıları ve kopyalanabilir kurulum komutları.
- Çevrimdışı açılan paket bilgileri; yalnız istendiğinde arka planda GitHub
  sürüm kontrolü. Ağ hataları mevcut bağlantıları silmez.
- Geniş ekranda dört donanım kartı; dar ekranda iki sütun ve alt alta direksiyon
  panelleri. Altı görünüm 960×620 ve 1280×900 boyutlarında kontrol edilir.
- Teşhis kontrol sayıları ve doğrulanamayan sonuçları da koruyan dikkat filtresi.
- Türkçe/İngilizce geçişinde paket seçimi ve kaydedilmemiş değerler korunur.
- `Ctrl+L` ile bölümün indirme sayfası ve yerel klavye kısayolları penceresi.

Geçişler, kart belirmeleri ve tarama sonrası otomatik kaydırma hareket azaltma
tercihine uyar. Canlı giriş değerleri geciktirilmez. Kurulum komutları yalnız
gösterilir/kopyalanır; uygulama tarafından çalıştırılmaz. Fiziksel kuvvet geri
bildirimi için yeni cihaz doğrulaması yapıldığı iddia edilmez.

Manrope, OFL-1.1 lisansı ve telif bildirimiyle pakete dahildir. Font yalnız
uygulama sürecinde yüklenir; sistem font kurulumu gerekmez.

İzole Fedora 44/GTK/Wayland ortamında 200 test geçti; arayüz testleri atlanmadı.

Fedora 44 için noarch RPM, kaynak RPM, kaynak arşivi ve SHA-256 sağlama toplamları
GitHub Releases üzerinden sunulur.

## English

The three native modules now share bundled Manrope typography, a calmer sidebar,
clear visual hierarchy and responsive monochrome dashboards. Each module has
its own official download page with available package formats, release links
and copyable manual-install commands. Download metadata works offline; release
checks are explicit asynchronous requests. Diagnostics add summary counts and
an attention filter that retains unverified results. Language changes preserve
package choices and unapplied settings. Existing reduced-motion and explicit
device-write boundaries remain in place.

---

## 0.1.2 — donanım animasyonları

Donanım sayfasına devre ışıkları, yumuşak bir CPU halesi ve güncel pozitif RPM okumasıyla dönen temsili fan eklendi. 30 FPS sınırı, eski/başarısız ölçümde durma, gizli bölüm/pencere ve hareket azaltma kontrolleri vardır. Donanım yazma davranışı değişmedi. İzole GTK/Wayland ortamında 183 test geçti; fiziksel fan doğrulaması değildir.

# Linux Control 0.1.1 — genel animasyon güncellemesi

Animasyonlar Donanım, Direksiyon ve Sorun Teşhisi bölümlerinin tamamına yayıldı.

- Bölümler arasında yönüne göre kayan geçiş.
- Kartlarda kısa, kademeli belirme ve hover vurgusu.
- Düğme simgelerinde hafif büyüme/basma tepkisi; düğmeler, seçim listeleri, kaydırıcılar, anahtarlar ve arama alanlarında yumuşak geri bildirim.
- Ayrıntı bölümlerinde hem açılış hem kapanış geçişi. Kaydedilmemiş kontrol değerleri korunur.
- Açılır menülerde kısa belirme ve klavye kullanımında belirgin odak.
- Hareket azaltma ve masaüstünün animasyon tercihi, devam eden geçişleri sonlandırır. Masaüstü tercihi değişimi uygulama açıkken izlenir.
- Desteklenen küçük pencere boyutuna sığan daha kompakt yan panel.

Kart animasyonları tamamlanınca kare geri çağrıları kaldırılır. Canlı direksiyon ve pedal değerleri geciktirilmez. Donanım okumaları, profil akışları ve açık Uygula işlemleri korunur.

180 test izole Fedora 44/Wayland ortamında geçti. Otomatik testler sahte cihazlar kullanır; fiziksel kuvvet geri bildirimi doğrulaması değildir. Fedora RPM, kaynak RPM, kaynak arşivi ve SHA-256 sağlama toplamları sağlanır.

## English

Animation coverage now spans all three pages: directional navigation, staggered card entrances, card hover feedback, subtle icon hover/press responses, control focus transitions, popover fades and smoothly opening/closing details.

Unsaved values survive expansion and navigation. Reduce Motion and live desktop preference changes finish decorative transitions immediately. Completed entrances release their frame callbacks. Wheel telemetry remains immediate. The sidebar now fits the supported minimum window size.

The isolated Fedora 44 GTK suite contains 180 passing tests using simulated devices. Physical force-feedback and unsupported hardware coverage remain as described in the README.
