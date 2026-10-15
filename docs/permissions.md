# Donanım izinleri

Uzeyir Control normal kullanıcı olarak çalışır. Otomatik `sudo`, otomatik izin genişletme veya başlangıçta donanım ayarı değiştirme yapmaz.

## Direksiyon

Canlı giriş için kullanıcının ilgili `/dev/input/event*` aygıtını okuyabilmesi gerekir. Modern masaüstlerinde udev/logind `uaccess` bu erişimi etkin oturuma sağlayabilir. Ayarlar ayrıca HID sürücüsünün ilgili sysfs dosyalarına yazma izni gerektirir. Uygulama her ayarın destek ve izin durumunu gösterir; izin yoksa o kontrol salt okunur kalır.

Mevcut Wheel Control RPM'inin kurduğu Logitech udev kuralları varsa uygulama bunlardan yararlanır. Bu birleşik RPM sistem geneline yeni yazma izinleri kurmaz. Orijinal Wheel Control izin kuralı desteklenen Logitech cihazlarının belirli sysfs ayarlarını yerel kullanıcılara yazılabilir yapar; bu nedenle genel `chmod` yerine yalnız gerekli modele/ayara yönelik dağıtım veya yönetici yapılandırması tercih edilmelidir. Değişen udev erişiminin etkili olması için aygıtı yeniden bağlamak gerekebilir.

Profil yüklemek ayarları yalnız arayüze taşır. **Uygula**, cihaz ayarlarını açıkça gönderir. Uyumluluk modu geçişi ayrı bir onay penceresiyle başlar; aygıt yeniden bağlanabilir ve kalibrasyon hareketi yapabilir.

## Fanlar

Fan izleme yönetici yetkisi istemez. Fan yazımı mevcut Anvil Control RPM'i tarafından kurulmuş `/usr/libexec/anvil-fan-helper` ile sınırlıdır. Birleşik uygulama yardımcının normal bir dosya olduğunu, root sahipli olduğunu ve grup/diğer kullanıcılarca yazılamadığını kontrol eder. Anakart, kontrolcü ve kanal komut gönderilirken tekrar doğrulanır. Yardımcı bağımsız doğrulama, yedekleme, geri okuma ve geri alma kurallarını korur; polkit yetkilendirmesi açık fan işlemi sırasında gerekebilir.

Desteklenmeyen anakartta ya da yardımcı bulunmadığında fan değiştirme düğmeleri kapalıdır; sıcaklık ve devir izleme çalışmaya devam eder. Yardımcıyı kullanıcı tarafından yazılabilir bir konuma kopyalayarak bu kontrolü aşmayın.

## Güç profili ve RGB

Güç profilleri sistemdeki power-profiles-daemon hizmetinin sunduğu seçeneklerden gelir. Yetkilendirme sistem politikasına bağlıdır. RGB, kurulu OpenRGB ve erişilebilir cihazlarla sınırlıdır. OpenRGB taraması ya da renk/mod uygulaması yalnız kullanıcı bu eylemi seçtiğinde yapılır.

## SSD ve teşhis

SSD taraması UDisks2'nin mevcut önbelleğini okur. SMART yenilemez, kendi kendini test komutu göndermez ve etkileşimli yetkilendirme istemez. Eksik, eski veya erişilemeyen verinin yerine sağlık yüzdesi tahmin etmez. Sistem ve Flatpak kontrolleri salt okunur komutlarla yapılır.
