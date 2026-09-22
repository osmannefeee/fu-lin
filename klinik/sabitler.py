# -*- coding: utf-8 -*-
"""Tüm sabitler tek yerde."""
TARIH_FMT = "%Y-%m-%d"
SAAT_FMT = "%H:%M"

TEDAVI_FIYAT = {
    "Muayene": 0,
    "Diş Temizliği (Detertraj)": 2500,
    "Dolgu": 3500,
    "Kanal Tedavisi": 8000,
    "Diş Çekimi": 3000,
    "Gömülü Diş Çekimi": 7000,
    "İmplant": 35000,
    "Porselen Kron": 12000,
    "Zirkonyum Kron": 15000,
    "Ortodonti (Diş Teli)": 60000,
    "Lamina / Estetik": 14000,
    "Protez": 20000,
    "Çocuk Diş Tedavisi": 2500,
    "Diğer": 0,
}

DISLER_UST = ["18", "17", "16", "15", "14", "13", "12", "11",
              "21", "22", "23", "24", "25", "26", "27", "28"]
DISLER_ALT = ["48", "47", "46", "45", "44", "43", "42", "41",
              "31", "32", "33", "34", "35", "36", "37", "38"]
DIS_DURUMLARI = ["Sağlam", "Çürük", "Dolgulu", "Kanal", "Kron",
                 "İmplant", "Çekilmiş", "Eksik", "Planlandı"]
DURUM_RENK = {
    "Sağlam": "#ffffff", "Çürük": "#ef4444", "Dolgulu": "#3b82f6",
    "Kanal": "#a855f7", "Kron": "#f59e0b", "İmplant": "#10b981",
    "Çekilmiş": "#64748b", "Eksik": "#e2e8f0", "Planlandı": "#fde68a",
}

KART_RENKLERI = ["#0ea5e9", "#8b5cf6", "#f59e0b", "#10b981"]
ROLLER = ["admin", "hekim", "sekreter"]

RANDEVU_DURUM = ["Planlandı", "Geldi", "Gelmedi", "İptal"]
TEDAVI_DURUM = ["Planlandı", "Devam Ediyor", "Tamamlandı"]
ODEME_YONTEM = ["Nakit", "Kredi Kartı", "Havale/EFT", "Senet", "Diğer"]
GIDER_KATEGORI = ["Kira", "Personel", "Malzeme", "Cihaz", "Fatura", "Vergi", "Diğer"]

DENEME_GUN = 14
LISANS_SECRET = "FuLin-2026-Gizli"
LISANS_TEL = "0551 194 78 40"
WA_NO = "905511947840"
