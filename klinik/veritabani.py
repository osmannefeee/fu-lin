# -*- coding: utf-8 -*-
"""SQLite katmanı. Şema değişirse burası + migrasyon güncellenir."""
import os
import sqlite3
import sys

from .sabitler import TARIH_FMT  # noqa: F401 (belge amaçlı)
from .yardim import sifre_hashla  # döngüsel import yok: yardim veritabani'ni kullanmaz


def uygulama_dizini():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DB_ADI = os.path.join(uygulama_dizini(), "klinik.db")


class Veritabani:
    def __init__(self, db_path=DB_ADI):
        self.db_path = db_path
        self.baglan = sqlite3.connect(db_path)
        self.baglan.row_factory = sqlite3.Row
        self.tablolari_kur()

    def tablolari_kur(self):
        c = self.baglan.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS hastalar(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT NOT NULL, tc TEXT, telefon TEXT,
            dogum TEXT, cinsiyet TEXT, adres TEXT,
            alerji TEXT, kronik TEXT, notlar TEXT,
            kayit_tarih TEXT DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS hekimler(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_soyad TEXT NOT NULL, brans TEXT, telefon TEXT, aktif INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS randevular(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hasta_id INTEGER NOT NULL, hekim_id INTEGER,
            tarih TEXT NOT NULL, saat TEXT NOT NULL,
            islem TEXT, durum TEXT DEFAULT 'Planlandı', notlar TEXT,
            FOREIGN KEY(hasta_id) REFERENCES hastalar(id),
            FOREIGN KEY(hekim_id) REFERENCES hekimler(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS tedaviler(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hasta_id INTEGER NOT NULL, hekim_id INTEGER,
            tarih TEXT NOT NULL, dis_no TEXT, islem TEXT,
            adet INTEGER DEFAULT 1, birim_ucret REAL DEFAULT 0,
            toplam_ucret REAL DEFAULT 0, durum TEXT DEFAULT 'Planlandı', notlar TEXT,
            FOREIGN KEY(hasta_id) REFERENCES hastalar(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS odemeler(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hasta_id INTEGER NOT NULL, tedavi_id INTEGER,
            tarih TEXT NOT NULL, tutar REAL NOT NULL,
            yontem TEXT, aciklama TEXT,
            FOREIGN KEY(hasta_id) REFERENCES hastalar(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS stok(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun TEXT NOT NULL, kategori TEXT, miktar REAL DEFAULT 0,
            birim TEXT DEFAULT 'Adet', kritik_seviye REAL DEFAULT 5,
            son_guncelleme TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS giderler(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL, kategori TEXT, tutar REAL NOT NULL, aciklama TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS kullanicilar(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT UNIQUE NOT NULL, sifre_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'sekreter', ad_soyad TEXT, aktif INTEGER DEFAULT 1)""")
        c.execute("""CREATE TABLE IF NOT EXISTS dis_durum(
            hasta_id INTEGER NOT NULL, dis_no TEXT NOT NULL,
            durum TEXT DEFAULT 'Sağlam', notlar TEXT,
            PRIMARY KEY(hasta_id, dis_no))""")
        c.execute("""CREATE TABLE IF NOT EXISTS sms_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL, hasta_id INTEGER, telefon TEXT,
            mesaj TEXT, durum TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ayarlar(
            anahtar TEXT PRIMARY KEY, deger TEXT)""")
        self.baglan.commit()
        c.execute("SELECT COUNT(*) s FROM hekimler")
        if c.fetchone()["s"] == 0:
            c.executemany("INSERT INTO hekimler(ad_soyad, brans, telefon) VALUES(?,?,?)", [
                ("Dr. Örnek Hekim", "Genel Diş Hekimi", "0500 000 00 00"),
                ("Dr. Ayşe Yılmaz", "Ortodonti", "0500 000 00 01"),
            ])
        c.execute("SELECT COUNT(*) s FROM kullanicilar")
        if c.fetchone()["s"] == 0:
            c.execute("INSERT INTO kullanicilar(kullanici_adi, sifre_hash, rol, ad_soyad) VALUES(?,?,?,?)",
                      ("admin", sifre_hashla("admin123"), "admin", "Yönetici"))
        for anahtar, deger in [
            ("klinik_adi", "Özel Diş Sağlığı Merkezi"),
            ("sms_sablon", "Sayın {hasta}, {tarih} {saat} tarihinde {klinik} randevunuz vardır. Sağlıklı günler dileriz."),
            ("netgsm_user", ""),
            ("netgsm_pass", ""),
            ("netgsm_header", ""),
            ("lisans_tipi", "deneme"),
            ("lisans_musteri", ""),
            ("lisans_anahtar", ""),
            ("kurulum_kodu", ""),
            ("kurulum_tarihi", ""),
        ]:
            c.execute("INSERT OR IGNORE INTO ayarlar(anahtar, deger) VALUES(?,?)", (anahtar, deger))
        self.baglan.commit()

    def sorgu(self, sql, params=()):
        cur = self.baglan.cursor()
        cur.execute(sql, params)
        self.baglan.commit()
        return cur

    def listele(self, sql, params=()):
        cur = self.baglan.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
