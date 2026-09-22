# -*- coding: utf-8 -*-
"""SQLite katmanı: profil başına ayrı dosya (tamir_<profil>.db)."""
import os
import sqlite3
import sys


def uygulama_dizini():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Veritabani:
    def __init__(self, db_adi):
        self.db_path = os.path.join(uygulama_dizini(), db_adi)
        self.baglan = sqlite3.connect(self.db_path)
        self.baglan.row_factory = sqlite3.Row
        self.tablolari_kur()

    def tablolari_kur(self):
        c = self.baglan.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS musteriler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT NOT NULL,
            telefon TEXT, adres TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS is_emirleri(
            id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER NOT NULL,
            cihaz_tur TEXT, marka TEXT, model TEXT, seri TEXT, garanti TEXT,
            birim TEXT, ariza TEXT, yapilan TEXT,
            iscilik REAL DEFAULT 0, parca_tutar REAL DEFAULT 0,
            toplam REAL DEFAULT 0, durum TEXT DEFAULT 'Alındı',
            gelis TEXT, teslim TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS emir_parca(
            id INTEGER PRIMARY KEY AUTOINCREMENT, emir_id INTEGER NOT NULL,
            urun TEXT, adet REAL DEFAULT 1, fiyat REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS parcalar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, urun TEXT UNIQUE,
            miktar REAL DEFAULT 0, kritik REAL DEFAULT 2, fiyat REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS odemeler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, emir_id INTEGER,
            musteri_id INTEGER, tarih TEXT, tutar REAL, yontem TEXT, aciklama TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS faturalar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, emir_id INTEGER UNIQUE,
            no TEXT UNIQUE, tarih TEXT, ara_toplam REAL, kdv_oran REAL,
            kdv REAL, genel REAL, durum TEXT DEFAULT 'Kesildi')""")
        c.execute("""CREATE TABLE IF NOT EXISTS sms_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, telefon TEXT,
            mesaj TEXT, durum TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ayarlar(
            anahtar TEXT PRIMARY KEY, deger TEXT)""")
        self.baglan.commit()
        for anahtar, deger in [
            ("profil", ""), ("isletme", "Servisim"),
            ("sms_sablon", "Sayın {ad}, {no} nolu servis kaydınız {durum} aşamasında. - {isletme}"),
            ("lisans_tipi", "deneme"), ("lisans_musteri", ""), ("lisans_anahtar", ""),
            ("kurulum_kodu", ""), ("kurulum_tarihi", ""),
        ]:
            c.execute("INSERT OR IGNORE INTO ayarlar(anahtar, deger) VALUES(?,?)", (anahtar, deger))
        self.baglan.commit()

    def sorgu(self, sql, params=()):
        cur = self.baglan.cursor()
        cur.execute(sql, params)
        self.baglan.commit()
        return cur

    def listele(self, sql, params=()):
        return self.baglan.cursor().execute(sql, params).fetchall()
