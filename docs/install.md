# Uzeyir Control — Linux kurulumları

[GitHub Releases](https://github.com/Tubix777/linux-control/releases/tag/v0.3.1)
sayfasından dağıtımınıza uygun dosyayı indirin. Paketler üçüncü parti bir mağazaya
yüklenmiş değildir; bu projenin kendi GitHub yayınıdır.

| Dağıtım | İndirilecek dosya | Gereken sürüm |
| --- | --- | --- |
| Ubuntu, Kubuntu ve Ubuntu tabanlı sistemler | `uzeyir-control_0.3.1-1_all.deb` | Ubuntu 24.04 veya 26.04 |
| Zorin OS | Aynı `.deb` | Zorin 18 serisi (Ubuntu 24.04 tabanı) |
| Deepin | Aynı `.deb` | Deepin 25; gerekli kütüphaneler sistem deposunda bulunmalı |
| Debian | Aynı `.deb` | Debian 13 veya eşdeğer bağımlılıklar |
| Arch Linux | `uzeyir-control-0.3.1-1-any.pkg.tar.zst` | Güncel, tam yükseltilmiş Arch |
| Fedora | `uzeyir-control-0.3.1-1.fc44.noarch.rpm` | Fedora 44 |
| Diğer dağıtımlar | `uzeyir-control-0.3.1.tar.gz` | Python ≥ 3.11, GTK ≥ 4.12, libadwaita ≥ 1.5 |

DEB `all`, Arch `any` ve Fedora `noarch` paketleri derlenmiş işlemci kodu içermez;
Python kaynaklarını ve arayüz varlıklarını taşır. Bu, her işlemci/cihazın gerçek
donanımla doğrulandığı anlamına gelmez. Düşük sürümlü dağıtımlarda bağımlılık
kontrollerini atlamayın veya sistem kütüphanelerini elle değiştirmeyin.

## Ubuntu / Zorin / Deepin / Debian

İndirilen dosyanın bulunduğu klasörde:

```bash
sudo apt install ./uzeyir-control_0.3.1-1_all.deb
```

APT, Python/GTK/libadwaita bağımlılıklarını kendi dağıtımınızın depolarından
çözer. Ubuntu 22.04, Zorin 17 ve Deepin 23 için bu sürümün kütüphane tabanı
hedeflenmemiştir. Paket yöneticisi karşılanmayan bağımlılık bildirirse kurulumu
zorlamayın. Gerekli paket sürümlerini görmek için:

```bash
apt-cache policy python3 gir1.2-gtk-4.0 gir1.2-adw-1
```

## Arch Linux

Önce sistemi ve bağımlılıkları birlikte güncelleyin; ardından indirdiğiniz
GitHub paketini kurun:

```bash
sudo pacman -Syu --needed python python-gobject python-cairo python-pyudev gtk4 libadwaita fontconfig
sudo pacman -U ./uzeyir-control-0.3.1-1-any.pkg.tar.zst
```

Kaynak tarifiyle kurmak için `uzeyir-control-0.3.1-arch-build.tar.gz` dosyasını
indirin. Paket, PKGBUILD ile tam eşleşen kaynak arşivini ve SHA-256 değerini içerir:

```bash
sudo pacman -Syu --needed base-devel
tar -xzf uzeyir-control-0.3.1-arch-build.tar.gz
cd uzeyir-control-0.3.1-arch-build
less PKGBUILD
makepkg -si
```

`makepkg` normal kullanıcı olarak çalıştırılır. Bu paket AUR'a veya Arch'ın
resmî deposuna yüklenmiş değildir. Arch türevlerinde paket ve kütüphane sürümleri
ayrıca kontrol edilmelidir.

## Fedora

```bash
sudo dnf install ./uzeyir-control-0.3.1-1.fc44.noarch.rpm
```

`.src.rpm` yeniden derleme içindir; normal kullanımda `.noarch.rpm` dosyasını seçin.

## Açma, güncelleme ve kaldırma

Uygulama menüsünden **Uzeyir Control**'ü açın veya `uzeyir-control` çalıştırın.
Uygulamanın kendisini yönetici olarak çalıştırmayın. Eski `linux-control` komutu,
masaüstü kimliği, dil/hareket tercihleri ve Wheel profilleri uyumluluk için korunur.
Yeni paket, eski `linux-control` paketinin yerine geçer. Kullanıcı profilleri
kaldırma işleminin parçası olarak silinmez.

```bash
sudo apt remove uzeyir-control       # DEB sistemleri
sudo pacman -R uzeyir-control        # Arch
sudo dnf remove uzeyir-control       # Fedora
```

İsteğe bağlı `udisks2` SSD verisi, `flatpak` uygulama teşhisi ve `lm-sensors` /
`lm_sensors` ek sensör okumaları sağlar. NVIDIA/OpenRGB/güç profili özellikleri
kendi sürücü veya hizmetlerine bağlıdır. RPM depo kontrolü APT/pacman depolarını
doğrulamaz. Yeni paketler yönetici yardımcısı, otomatik servis veya geniş cihaz
izinleri kurmaz; mevcut donanım güvenlik sınırları korunur.

## Dosya doğrulama

İndirdiğiniz dosyayla `SHA256SUMS` dosyasını aynı klasöre koyun:

```bash
sha256sum --ignore-missing -c SHA256SUMS
```

En az indirdiğiniz dosya için `OK` sonucu görülmelidir. Sağlama toplamı
kriptografik yayıncı imzası değildir; dosyaları projenin resmî GitHub yayınından alın.

## English

Use the DEB for Ubuntu 24.04/26.04, Zorin 18 and Deepin 25 with Python ≥ 3.11,
GTK ≥ 4.12 and libadwaita ≥ 1.5. Use the pacman package or included offline
PKGBUILD/source bundle on current Arch, and the noarch RPM on Fedora 44.
These are upstream GitHub assets, not AUR/Flathub/store listings. Install with
your distribution's package manager, then launch **Uzeyir Control** without sudo.
The old desktop identity, preferences, profiles and `linux-control` command are
retained. Check SHA256SUMS and consult validation.md for the actual test scope.

Zorin's base is documented at https://zorin.com/os/details/; Arch's package
recipe format is documented at https://man.archlinux.org/man/PKGBUILD.5.en.
