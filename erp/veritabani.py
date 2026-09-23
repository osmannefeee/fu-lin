# -*- coding: utf-8 -*-
import os
import sqlite3
import sys


def uygulama_dizini():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Veritabani:
    def __init__(self, db_adi="erp.db"):
        self.db_path = os.path.join(uygulama_dizini(), db_adi)
        self.baglan = sqlite3.connect(self.db_path)
        self.baglan.row_factory = sqlite3.Row
        self.tablolari_kur()

    def tablolari_kur(self):
        c = self.baglan.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS urunler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, kod TEXT UNIQUE, ad TEXT NOT NULL,
            kategori TEXT, birim TEXT DEFAULT 'Adet',
            alis_fiyat REAL DEFAULT 0, satis_fiyat REAL DEFAULT 0,
            miktar REAL DEFAULT 0, kritik REAL DEFAULT 5)""")
        c.execute("""CREATE TABLE IF NOT EXISTS cariler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tip TEXT DEFAULT 'Müşteri',
            unvan TEXT NOT NULL, yetkili TEXT, telefon TEXT, adres TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS faturalar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tip TEXT, no TEXT UNIQUE,
            cari_id INTEGER, tarih TEXT, ara_toplam REAL, kdv_oran REAL,
            kdv REAL, genel REAL, durum TEXT DEFAULT 'Açık')""")
        c.execute("""CREATE TABLE IF NOT EXISTS fatura_kalem(
            id INTEGER PRIMARY KEY AUTOINCREMENT, fatura_id INTEGER,
            urun_id INTEGER, urun TEXT, adet REAL DEFAULT 1, fiyat REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS stok_hareket(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, urun_id INTEGER,
            degisim REAL, neden TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS hesaplar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT UNIQUE, tur TEXT DEFAULT 'Kasa')""")
        c.execute("""CREATE TABLE IF NOT EXISTS kasa_hareket(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, hesap_id INTEGER,
            yon TEXT, tutar REAL, cari_id INTEGER, aciklama TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ayarlar(
            anahtar TEXT PRIMARY KEY, deger TEXT)""")
        self.baglan.commit()
        for anahtar, deger in [
            ("isletme", "Şirketim"),
            ("lisans_tipi", "deneme"), ("lisans_musteri", ""), ("lisans_anahtar", ""),
            ("kurulum_kodu", ""), ("kurulum_tarihi", ""),
        ]:
            c.execute("INSERT OR IGNORE INTO ayarlar(anahtar, deger) VALUES(?,?)", (anahtar, deger))
        self.baglan.commit()
        if not c.execute("SELECT COUNT(*) s FROM hesaplar").fetchone()["s"]:
            c.executemany("INSERT INTO hesaplar(ad,tur) VALUES(?,?)",
                          [("Merkez Kasa", "Kasa"), ("Banka", "Banka")])
            self.baglan.commit()

    def sorgu(self, sql, params=()):
        cur = self.baglan.cursor()
        cur.execute(sql, params)
        self.baglan.commit()
        return cur

    def listele(self, sql, params=()):
        return self.baglan.cursor().execute(sql, params).fetchall()
