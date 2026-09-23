# -*- coding: utf-8 -*-
import os
import sqlite3
import sys


def uygulama_dizini():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Veritabani:
    def __init__(self, db_adi="crm.db"):
        self.db_path = os.path.join(uygulama_dizini(), db_adi)
        self.baglan = sqlite3.connect(self.db_path)
        self.baglan.row_factory = sqlite3.Row
        self.tablolari_kur()

    def tablolari_kur(self):
        c = self.baglan.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS musteriler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, firma TEXT, yetkili TEXT,
            telefon TEXT, eposta TEXT, adres TEXT, kaynak TEXT, etiket TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS firsatlar(
            id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER NOT NULL,
            baslik TEXT, tutar REAL DEFAULT 0, olasilik INTEGER DEFAULT 10,
            asama TEXT DEFAULT 'Aday', kapanis TEXT, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS aktiviteler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, firsat_id INTEGER,
            tur TEXT, tarih TEXT, ozet TEXT, sonuc TEXT, takip TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS teklifler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, firsat_id INTEGER,
            no TEXT UNIQUE, tarih TEXT, durum TEXT DEFAULT 'Taslak',
            kdv_oran REAL DEFAULT 20, notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS teklif_kalem(
            id INTEGER PRIMARY KEY AUTOINCREMENT, teklif_id INTEGER,
            aciklama TEXT, adet REAL DEFAULT 1, fiyat REAL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS gorevler(
            id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, musteri_id INTEGER,
            bitis TEXT, durum TEXT DEFAULT 'Bekliyor', notlar TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS sms_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, telefon TEXT,
            mesaj TEXT, durum TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ayarlar(
            anahtar TEXT PRIMARY KEY, deger TEXT)""")
        self.baglan.commit()
        for anahtar, deger in [
            ("isletme", "Şirketim"),
            ("sms_sablon", "Merhaba {ad}, {isletme} ile görüşmemizi hatırlatmak istedik."),
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
