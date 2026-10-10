# Linux Control

Anvil Control, Wheel Control ve Fedora Doctor tek bir yerel GTK 4 / libadwaita penceresinde. Soldaki büyük düğmelerle **Donanım**, **Direksiyon** ve **Sorun Teşhisi** arasında geçiş yapın.

Siyah, gri ve beyaz arayüz; akıcı bölüm geçişleri; tarama sonrası sonuçlara yumuşak kaydırma; ekrana giren bulgu kartlarında kademeli belirme. Türkçe ve İngilizce arasında uygulamayı yeniden başlatmadan geçiş yapılır. **Hareketi azalt** tercihi geçişleri ve kaydırma animasyonlarını kapatır; canlı giriş verileri anında güncellenir.

0.1.1 ile animasyonlar üç bölüme de yayıldı: bölüm geçişlerinde kayma, kartlarda kısa ve kademeli belirme, düğme/simge/kaydırıcı/arama alanlarında hover ve odak tepkileri, menülerde belirme ve ayrıntılarda akıcı açılıp kapanma. Masaüstünün animasyon tercihi uygulama açıkken değiştirildiğinde anında izlenir. Animasyonlar sona erince kare geri çağrıları bırakılır; direksiyon ölçümleri anlık kalır. Klavyeyle kullanılan kontrollerin odak çerçevesi korunur.

Bu ilk birleşik sürüm ön sürümdür. Donanım verileri gerçek yerel kaynaklardan okunur; demo direksiyon yalnızca kullanıcı açıkça seçtiğinde gösterilir. Desteklenmeyen veya erişilemeyen veri yerine uydurma sayı gösterilmez.

## Özellikler

0.1.2: Donanım başlığında hareketli devre ışıkları ve fan etkinlik görseli vardır. Fan yalnız güncel pozitif RPM okumasında döner; dönüş hızı temsili olup gerçek RPM ölçeği değildir. Pencere/bölüm gizlenince, ölçüm eskiyince veya izleme duraklatılınca animasyon durur.

| Bölüm | İşlevler |
| --- | --- |
| Donanım | CPU/GPU kullanımı ve sıcaklık, RAM ve disk kullanımı, canlı geçmiş grafiği, sensör arama, oturum minimum/maksimum değerleri, CSV/JSON dışa aktarma, isteğe bağlı sıcaklık bildirimi |
| Donanım kontrolleri | Sistemin sunduğu güç profilleri, OpenRGB üzerinden mevcut cihazların renk/mod seçimi, desteklenen anakartlarda mevcut Anvil yardımcısı üzerinden fan eğrisi/tam hız/geri alma |
| Direksiyon | Logitech cihaz keşfi ve hotplug, canlı direksiyon/pedal/tuş verileri, sürücünün sunduğu dönüş açısı ve kuvvet geri bildirimi kontrolleri, oyun profili yükleme/kaydetme/içe ve dışa aktarma |
| Sorun Teşhisi | Disk alanı, başarısız sistem/kullanıcı servisleri, NetworkManager durumu, RPM depo tanımları, NVMe SSD dayanıklılık tahmini, Flatpak kurulumu/çalışma ortamı/klasör erişimi |

Kontrol ayarları açık bir **Uygula** eylemiyle gönderilir. Bölüm ve dil değişimi ayarları donanıma uygulamaz. Teşhis taraması sistem ayarlarını değiştirmez, uygulama başlatmaz, ayrıcalık istemez ve günlükleri dışarı göndermez.

## Fedora'da çalıştırma

[Releases](https://github.com/Tubix777/linux-control/releases) sayfasındaki Fedora RPM'ini indirin ve paket yöneticinizle kurun. Ardından uygulama menüsünden **Linux Control**'ü açın.

Kaynak koddan çalıştırmak için dağıtım paketleri gerekir:

```bash
sudo dnf install python3-gobject python3-cairo python3-pyudev gtk4 libadwaita
./run.sh
```

Uygulamanın kendisini `sudo` ile çalıştırmayın. Kaynaktan çalıştırma setuptools veya pip kurulumu gerektirmez. GTK 4, libadwaita ve Python bağımlılıkları bulunduğunda diğer Linux dağıtımlarında da çalışabilir; Fedora RPM başka dağıtımlara yönelik değildir.

```bash
./run.sh --page doctor
./run.sh --language en
./run.sh --page wheel --wheel-demo
```

`Ctrl+1`, `Ctrl+2`, `Ctrl+3` bölüm değiştirir. Dil ve hareket tercihleri kullanıcı ayarlarında saklanır. Direksiyon profilleri mevcut Wheel Control profil dosyasını kullanır; mevcut uygulamalar ve depolar korunur.

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

Linux Control combines hardware monitoring, racing-wheel controls and local system diagnostics in one native GTK 4 window, with shared monochrome styling, smooth navigation, scan-result animations and live Turkish/English switching. Reduce Motion respects accessibility preferences. Device settings require explicit actions; diagnostics remain read-only. Unavailable hardware data is never replaced with invented readings. This initial combined version is a preview; physical force-feedback coverage and motherboard fan control remain limited to the support described above.
