# -*- coding: utf-8 -*-
"""İş kolu profilleri: kurulumda seçilir, tüm ekranlar buna göre şekillenir."""
TARIH_FMT = "%Y-%m-%d"

PROFILLER = {
    "elektronik": {
        "ad": "TamirPro Elektronik",
        "slogan": "Beyaz Eşya & Elektronik Servisi",
        "renk": "#0ea5e9",
        "karsi_renk": "#0369a1",
        "birim_ad": "Tezgah",
        "birimler": ["Tezgah 1", "Tezgah 2", "Tezgah 3"],
        "db": "tamir_elektronik.db",
        "cihaz_turleri": ["Televizyon", "Buzdolabı", "Çamaşır Makinesi", "Bulaşık Makinesi",
                          "Fırın", "Klima", "Kombi", "Elektrikli Süpürge", "Diğer"],
        "alanlar": [("Marka", "marka"), ("Model", "model"), ("Seri No", "seri"),
                    ("Garanti Bitişi", "garanti")],
        "arizalar": ["Açılmıyor", "Ses yok", "Görüntü yok", "Su almıyor", "Isıtmıyor",
                     "Soğutmuyor", "Program hatası", "Diğer"],
        "islemler": {"Arıza Tespit": 500, "Kart Tamiri": 2500, "Motor Değişimi": 4000,
                     "Kompresör": 6000, "Genel Bakım": 1200, "Montaj": 800, "Diğer": 0},
        "durumlar": ["Alındı", "Arıza Tespit", "Parça Bekliyor", "Onarımda",
                     "Testte", "Hazır", "Teslim Edildi", "İptal"],
    },
    "otomotiv": {
        "ad": "TamirPro Otomotiv",
        "slogan": "Oto Bakım & Onarım",
        "renk": "#f59e0b",
        "karsi_renk": "#92400e",
        "birim_ad": "Lift",
        "birimler": ["Lift 1", "Lift 2", "Lift 3"],
        "db": "tamir_otomotiv.db",
        "cihaz_turleri": ["Otomobil", "Hafif Ticari", "Motosiklet", "Diğer"],
        "alanlar": [("Plaka", "marka"), ("Marka / Model", "model"), ("KM", "seri"),
                    ("Yakıt / Motor", "garanti")],
        "arizalar": ["Periyodik bakım", "Fren sorunu", "Motor arıza lambası", "Yağ kaçağı",
                     "Lastik/rot-balans", "Elektrik arızası", "Klima", "Diğer"],
        "islemler": {"Periyodik Bakım": 5000, "Yağ + Filtre": 2500, "Fren Balata": 4000,
                     "Triger Seti": 12000, "Debriyaj": 15000, "Klima Gazı": 2000, "Diğer": 0},
        "durumlar": ["Alındı", "Ekspertiz", "Parça Bekliyor", "Onarımda",
                     "Test Sürüşü", "Hazır", "Teslim Edildi", "İptal"],
    },
    "telefon": {
        "ad": "TamirPro Telefon-PC",
        "slogan": "Telefon & Bilgisayar Servisi",
        "renk": "#8b5cf6",
        "karsi_renk": "#4c1d95",
        "birim_ad": "Tezgah",
        "birimler": ["Tezgah 1", "Tezgah 2"],
        "db": "tamir_telefon.db",
        "cihaz_turleri": ["Akıllı Telefon", "Tablet", "Dizüstü PC", "Masaüstü PC", "Diğer"],
        "alanlar": [("Marka", "marka"), ("Model", "model"), ("IMEI / Seri No", "seri"),
                    ("Cihaz Şifresi", "garanti")],
        "arizalar": ["Ekran kırık", "Batarya", "Açılmıyor", "Şarj almıyor", "Kamera",
                     "Yazılım/format", "Sıvı teması", "Diğer"],
        "islemler": {"Ekran Değişimi": 4000, "Batarya Değişimi": 2000, "Yazılım/Format": 1000,
                     "Anakart Onarımı": 5000, "Kamera Değişimi": 2500, "Genel Bakım": 750, "Diğer": 0},
        "durumlar": ["Alındı", "Arıza Tespit", "Parça Bekliyor", "Onarımda",
                     "Testte", "Hazır", "Teslim Edildi", "İptal"],
    },
}

DENEME_GUN = 14
LISANS_SECRET = "FuLin-Tamir-2026"
LISANS_TEL = "0551 194 78 40"
WA_NO = "905511947840"
ODEME_YONTEM = ["Nakit", "Kredi Kartı", "Havale/EFT", "Diğer"]
