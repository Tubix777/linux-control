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
