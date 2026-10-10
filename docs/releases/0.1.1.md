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
