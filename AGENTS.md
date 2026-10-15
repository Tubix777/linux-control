# Çalışma ve yayın tercihleri

- Kullanıcı Türkçe iletişim, siyah/gri/beyaz görünüm, akıcılık ve animasyonlara önem veriyor.
- Donanım, Direksiyon ve Sorun Teşhisi tek yerel GTK4/libadwaita penceresinde kalır.
- Rutin, geri alınabilir geliştirme kararlarını uygulayın; kullanıcı tekrar soru sorulmasını istemiyor.
- Her tamamlanan güncellemede ilgili testleri çalıştırın, sürümü artırın, kaynakları
  Tubix777/linux-control deposunda ve sürümlü Fedora RPM/kaynak paketini GitHub Releases'ta yayımlayın.
- Kullanıcının yeni talimatları yayın tercihini değiştirebilir; bunları önceliklendirin.
- Ölçüm, keşif ve dosya işlemleri GTK ana döngüsünü bloke etmemelidir.
- Dil değişimi ve bölüm geçişleri kullanıcıdaki kaydedilmemiş değerleri korur ve donanıma yazmaz.
- Hareket azaltma ve masaüstünün animasyon tercihi dikkate alınır.
- Fan yazımı yalnız Anvil'in mevcut root sahipli paketli yardımcısıyla ve doğrulanmış
  anakart/kanal sınırlarıyla yapılır. Yeni ayrıcalıklı yardımcı veya geniş izin eklemeyin.
- Seri numaralarını, kişisel günlükleri, kullanıcı tanılama dosyalarını veya kimlik bilgilerini commit etmeyin.
- Simülasyon ve gerçek cihaz doğrulamasını ayırın; belirsiz sağlık verisini sayı olarak uydurmayın.

- Ana uygulama adı Uzeyir Control, teşhis modülünün adı Uzeyir Doctor; kurulum paketleri ve ana komut uzeyir-control. Eski Python modülü, ayar dizini, masaüstü kimliği ve linux-control komutu uyumluluk için korunur.
- Yayınlar Fedora RPM/kaynak RPM, Ubuntu/Deepin/Zorin DEB, Arch pacman ve sabit checksumlu PKGBUILD/kaynak paketini içerir. CI her dağıtımda kurulu altı görünümü ve SVG yükleyicisini doğrular; gerçek masaüstü/donanım testini konteyner doğrulamasından ayırın.
- Sürüm artırıldığında pyproject.toml içindeki source-date-epoch değerini de yayın zamanına ilerletin; sabit kaynak zamanı yeniden üretilebilirliği ve Python önbelleğinin sürümler arasında yenilenmesini sağlar.
