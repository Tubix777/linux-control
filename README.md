# Linux Control

Anvil Control, Wheel Control ve Fedora Doctor tek bir yerel GTK 4 / libadwaita penceresinde. Soldaki büyük düğmelerle **Donanım**, **Direksiyon** ve **Sorun Teşhisi** arasında geçiş yapın.

Siyah, gri ve beyaz arayüz; akıcı bölüm geçişleri; tarama sonrası sonuçlara yumuşak kaydırma; ekrana giren bulgu kartlarında kademeli belirme. Türkçe ve İngilizce arasında uygulamayı yeniden başlatmadan geçiş yapılır. **Hareketi azalt** tercihi geçişleri ve kaydırma animasyonlarını kapatır; canlı giriş verileri anında güncellenir.

**0.2.1:** Bölüm ve indirme sayfaları yönüne göre kayar. Başlıklar, donanım kartları, paket satırları ve kurulum komutları kademeli hareketle belirir. Gerçek tarama boyunca çalışan sinyal, işlem bitince kısa bir halka gösterir; bulgu içerikleri yükselerek görünür. Gizli sayfalarda etkinlik durur ve hareket azaltma tercihi korunur.

**0.2.0:** Sayfalar, yerel Manrope yazı tipi, daha sakin kartlar ve ortak bilgi hiyerarşisiyle yeniden düzenlendi. Donanım kartları geniş pencerede dört, dar pencerede iki sütun kullanır. Direksiyon ayarları dar pencerede alt alta yerleşir. Sol menüde her uygulamanın yanındaki indirme düğmesi, o uygulamanın paket ve sürüm sayfasını açar.

Teşhis ekranındaki özet, tamamlanan/dikkat gerektiren/doğrulanamayan kontrolleri ayrı gösterir. **Dikkat gerektirenler** filtresi doğrulanamayan bulguları da korur. Kart belirmeleri, ayrıntı açılışları, odak tepkileri ve masaüstünün hareket azaltma tercihi ortak şekilde çalışır.

Bu sürüm ön sürümdür. Donanım verileri gerçek yerel kaynaklardan okunur; demo direksiyon yalnızca kullanıcı açıkça seçtiğinde gösterilir. Desteklenmeyen veya erişilemeyen veri yerine uydurma sayı gösterilmez.

## Özellikler

Donanım başlığında hareketli devre ışıkları ve fan etkinlik görseli vardır. Fan yalnız güncel pozitif RPM okumasında döner; dönüş hızı temsili olup gerçek RPM ölçeği değildir. Pencere/bölüm gizlenince, ölçüm eskiyince veya izleme duraklatılınca animasyon durur.

| Bölüm | İşlevler |
| --- | --- |
| Donanım | CPU/GPU kullanımı ve sıcaklık, RAM ve disk kullanımı, canlı geçmiş grafiği, sensör arama, oturum minimum/maksimum değerleri, CSV/JSON dışa aktarma, isteğe bağlı sıcaklık bildirimi |
| Donanım kontrolleri | Sistemin sunduğu güç profilleri, OpenRGB üzerinden mevcut cihazların renk/mod seçimi, desteklenen anakartlarda mevcut Anvil yardımcısı üzerinden fan eğrisi/tam hız/geri alma |
| Direksiyon | Logitech cihaz keşfi ve hotplug, canlı direksiyon/pedal/tuş verileri, sürücünün sunduğu dönüş açısı ve kuvvet geri bildirimi kontrolleri, oyun profili yükleme/kaydetme/içe ve dışa aktarma |
| Sorun Teşhisi | Disk alanı, başarısız sistem/kullanıcı servisleri, NetworkManager durumu, RPM depo tanımları, NVMe SSD dayanıklılık tahmini, Flatpak kurulumu/çalışma ortamı/klasör erişimi |
| İndirme sayfaları | Modüle özel resmî sürüm bağlantıları, mevcut RPM/DEB/taşınabilir/kaynak paketleri, kopyalanabilir kurulum komutları ve isteğe bağlı sürüm kontrolü |

Kontrol ayarları açık bir **Uygula** eylemiyle gönderilir. Bölüm ve dil değişimi ayarları donanıma uygulamaz. Teşhis taraması sistem ayarlarını değiştirmez, uygulama başlatmaz, ayrıcalık istemez ve günlükleri dışarı göndermez.

İndirme ekranları kayıtlı resmî paket bilgileriyle çevrimdışı açılır. **Güncel sürümü kontrol et** düğmesi yalnız ilgili GitHub deposunun herkese açık sürüm bilgilerini sorgular; arayüzü bekletmez. Ağ hatasında mevcut bağlantılar korunur. **İndir** ve sürüm bağlantıları varsayılan tarayıcıda açılır. Anvil ve Wheel bağlantıları bağımsız uygulamalara aittir; Fedora Doctor, birleşik Linux Control paketiyle dağıtılır. Manrope uygulama içinde yüklenir; masaüstünün yazı tipi ayarı değiştirilmez.

## Fedora'da çalıştırma

[Releases](https://github.com/Tubix777/linux-control/releases) sayfasındaki Fedora RPM'ini indirin ve paket yöneticinizle kurun. Ardından uygulama menüsünden **Linux Control**'ü açın.

Kaynak koddan çalıştırmak için dağıtım paketleri gerekir:

```bash
sudo dnf install python3-gobject python3-cairo python3-pyudev gtk4 libadwaita
./run.sh
```

Uygulamanın kendisini `sudo` ile çalıştırmayın. Kaynaktan çalıştırma setuptools veya pip kurulumu gerektirmez. GTK ≥ 4.12, libadwaita ≥ 1.5 ve Python ≥ 3.11 bağımlılıkları bulunduğunda diğer Linux dağıtımlarında da çalışabilir; Fedora RPM başka dağıtımlara yönelik değildir.

```bash
./run.sh --page doctor
./run.sh --language en
./run.sh --page wheel --wheel-demo
./run.sh --page hardware --downloads
```

`Ctrl+1`, `Ctrl+2`, `Ctrl+3` bölüm değiştirir; `Ctrl+L` mevcut bölümün indirme sayfasını açar. Başlıktaki klavye düğmesi kısayolları gösterir. Dil ve hareket tercihleri kullanıcı ayarlarında saklanır. Direksiyon profilleri mevcut Wheel Control profil dosyasını kullanır; mevcut uygulamalar ve depolar korunur.

## Donanım desteğinin sınırları

- GPU telemetrisi sürücüye bağlıdır. Kullanılamayan sensörler açıkça belirtilir.
- Fan yazımı yalnız **ASUS PRIME H610M-K D4**, doğrulanmış **NCT6798 kanal 1/2** ve root sahipli, grup/diğer kullanıcılarca yazılamayan **mevcut Anvil fan yardımcısı** ile açılır. Birleşik RPM yeni ayrıcalıklı yardımcı veya geniş sysfs izni kurmaz. Yardımcı bulunamazsa izleme çalışır, fan kontrolleri kapalı kalır.
- Direksiyon ayarları sürücünün sunduğu ve kullanıcıya yazma izni verdiği özelliklerle sınırlıdır. G29, asıl geliştirme cihazıdır; tanınan diğer modellerin her birinde tüm fiziksel kuvvet geri bildirimi davranışları doğrulanmış değildir. [İzinler](docs/permissions.md) kullanılabilir erişim yollarını açıklar.
- SSD'deki **Tahmini kalan ömür**, NVMe üreticisinin tahmini dayanıklılık kullanımından kalan paydır. Genel sağlık garantisi veya arıza olasılığı değildir. Kritik SMART uyarıları ayrı değerlendirilir. 24 saatten eski veya eksik veri yüzde olarak gösterilmez. SATA SSD için bu sürüm genel bir yüzde türetmez.
- NetworkManager bağlantı bilgisi internet erişimini kanıtlamaz. Depo tanımı kontrolü güncelleme işlemini ya da depo erişilebilirliğini test etmez. Flatpak izin kontrolü bir açılış hatasının nedenini tek başına kanıtlamaz.

## Geliştirme ve yayın

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 packaging/build_source.py
python3 packaging/build_rpm.py
```

Arayüz testleri gerçek masaüstü yerine ayrı bir sanal compositor altında çalıştırılmalıdır; [doğrulama belgesi](docs/validation.md) ayrıntıları içerir. GitHub Actions her değişiklikte testleri ve Fedora RPM derlemesini çalıştırır. Sürüm etiketi gönderildiğinde kaynak arşivi, RPM, kaynak RPM ve sağlama toplamları otomatik GitHub Release'e eklenir.

[Uygulama planı](PLAN.md), [yayın notları](docs/release-notes.md), [katkı ve lisanslar](ATTRIBUTION.md).

## English

Linux Control combines hardware monitoring, racing-wheel controls and local system diagnostics in one native GTK 4 window, with a shared monochrome design, bundled Manrope typography, responsive layouts, smooth navigation, scan-result animations and live Turkish/English switching. Each sidebar module has its own official download page. Package links work from bundled metadata offline; checking for newer releases is an explicit action. Installation commands can be copied but are never executed by the app. Reduce Motion respects accessibility preferences. Device settings require explicit actions; diagnostics remain read-only. Unavailable hardware data is never replaced with invented readings. This initial combined version is a preview; physical force-feedback coverage and motherboard fan control remain limited to the support described above.
