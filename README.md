# Fu-Lin — Hazır İşletme Yazılımları

## Klasörler
| Klasör | İçerik |
|---|---|
| `docs/` | Satış sitesi (GitHub Pages yayını buradan). `python docs/server.py` → site + admin panel (`/admin`) |
| `klinik/` | Diş Klinik Yönetim kaynak kodu (modüler paket) |
| `tamir/` | TamirPro kaynak kodu (elektronik / otomotiv / telefon-PC) |
| `docs/indir/` | Deneme exeleri (siteden indirilir) |

## Çalıştırma
- Diş Klinik: `python dis_klinik_yonetim.py` (giriş: admin / admin123)
- TamirPro: `python tamir_pro.py` (açılışta iş kolu seçilir)
- Site + panel: `python docs/server.py` → http://localhost:8000 ve http://localhost:8000/admin
- Lisans üretme: `python lisans_panel.py`

## Exe üretme
- `python -m PyInstaller --noconfirm --onefile --windowed --name DisKlinikYonetim --icon dis_ikon.ico --version-file version_info.txt dis_klinik_yonetim.py`
- `python -m PyInstaller --noconfirm --onefile --windowed --name TamirPro --icon tamir/tamir.ico --version-file tamir/tamir_version.txt tamir_pro.py`
- Kurulum paketleri: `DisKlinikKurulum.iss` ve `TamirPro_Kurulum.iss` (Inno Setup 6 ile derlenir)

## Yayın
GitHub Pages: repo Settings → Pages → Deploy from branch → `main` + `/docs`. Admin paneli (`server.py`) statik yayında çalışmaz; talepler o modda WhatsApp'a düşer.
