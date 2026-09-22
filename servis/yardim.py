# -*- coding: utf-8 -*-
from datetime import date, timedelta

from .sabitler import TARIH_FMT


def bugun():
    return date.today().strftime(TARIH_FMT)


def tl(x):
    try:
        return f"{float(x or 0):,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00 ₺"


def ayar(db, anahtar, deger=None):
    if deger is None:
        r = db.listele("SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,))
        return r[0]["deger"] if r else ""
    db.sorgu("INSERT OR REPLACE INTO ayarlar(anahtar, deger) VALUES(?,?)", (anahtar, deger))


def kayit_bakiye(db, kayit_id):
    top = db.listele("SELECT tutar t FROM kayitlar WHERE id=?", (kayit_id,))
    ode = db.listele("SELECT COALESCE(SUM(tutar),0) o FROM odemeler WHERE kayit_id=?", (kayit_id,))
    toplam = (top[0]["t"] if top else 0) or 0
    odenen = (ode[0]["o"] if ode else 0) or 0
    return toplam - odenen, toplam, odenen


def musteri_etiket(r):
    return f"{r['ad_soyad']} ({r['telefon'] or '-'}) [#{(r['id'])}]"


def musteri_sozluk(db):
    return {musteri_etiket(r): r["id"] for r in db.listele("SELECT * FROM musteriler ORDER BY ad_soyad")}


def garanti_durumu(bitis):
    """('bitmis'|'yaklasiyor'|'saglam', gun)"""
    if not bitis:
        return "yok", None
    try:
        gun = (date.fromisoformat(bitis) - date.today()).days
    except ValueError:
        return "yok", None
    if gun < 0:
        return "bitmis", gun
    if gun <= 30:
        return "yaklasiyor", gun
    return "saglam", gun


def sms_metni(db, ad, no, durum):
    try:
        return ayar(db, "sms_sablon").format(ad=ad, no=no, durum=durum, isletme=ayar(db, "isletme"))
    except (KeyError, IndexError, ValueError):
        return f"Sayın {ad}, {no} nolu kaydınız {durum} aşamasında."


def csv_yaz(klasor, ad, basliklar, satirlar):
    import csv
    import os
    yol = os.path.join(klasor, ad)
    with open(yol, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    return yol
