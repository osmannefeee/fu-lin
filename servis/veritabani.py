# -*- coding: utf-8 -*-
import os
import sqlite3
import sys


def uygulama_dizini():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Veritabani:
    def __init__(self, db_adi="servis.db"):
        self.db_path = os.path.join(uygulama_dizini(), db_adi)
        self.baglan = sqlite3.connect(self.db_path)
        self.baglan.row_factory = sqlite3.Row
        self.tablolari_kur()

    def tablolari_kur(self):
        c = self.baglan.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS musteriler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT NOT NULL,
            telefon TEXT, adres TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS teknisyenler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, telefon TEXT, aktif INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kayitlar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER NOT NULL,
            cihaz_tur TEXT, marka TEXT, model TEXT, seri TEXT,
            ariza TEXT, islem TEXT, teknisyen TEXT,
            garanti_var INTEGER DEFAULT 0, garanti_bitis TEXT,
            tutar REAL DEFAULT 0, durum TEXT DEFAULT 'Alındı',
            gelis TEXT, tahmini TEXT, teslim TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS parcalar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, urun TEXT UNIQUE,
            miktar REAL DEFAULT 0, kritik REAL DEFAULT 2, fiyat REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kayit_parca(
            id INTEGER PRIMARY KEY AUTOINCREMENT, kayit_id INTEGER,
            urun TEXT, adet REAL DEFAULT 1, fiyat REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS odemeler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, kayit_id INTEGER,
            musteri_id INTEGER, tarih TEXT, tutar REAL, yontem TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sms_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, telefon TEXT,
            mesaj TEXT, durum TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ayarlar(
            anahtar TEXT PRIMARY KEY, deger TEXT)""")
        self.baglan.commit()
        for anahtar, deger in [
            ("isletme", "Teknik Servisim"),
            ("sms_sablon", "Sayın {ad}, {no} nolu servis kaydınız {durum} aşamasında. - {isletme}"),
            ("lisans_tipi", "deneme"), ("lisans_musteri", ""), ("lisans_anahtar", ""),
            ("kurulum_kodu", ""), ("kurulum_tarihi", ""),
        ]:
            c.execute("INSERT OR IGNORE INTO ayarlar(anahtar, deger) VALUES(?,?)", (anahtar, deger))
        self.baglan.commit()
        if not c.execute("SELECT COUNT(*) s FROM teknisyenler").fetchone()["s"]:
            c.execute("INSERT INTO teknisyenler(ad) VALUES(?)", ("Teknisyen 1",))
            self.baglan.commit()

    def sorgu(self, sql, params=()):
        cur = self.baglan.cursor()
        cur.execute(sql, params)
        self.baglan.commit()
        return cur

    def listele(self, sql, params=()):
        return self.baglan.cursor().execute(sql, params).fetchall()
