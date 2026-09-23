# -*- coding: utf-8 -*-
from datetime import date, timedelta

from .sabitler import ASAMA_OLASILIK, TARIH_FMT


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


def musteri_etiket(r):
    ad = r["firma"] or r["yetkili"] or "?"
    return f"{ad} ({r['telefon'] or '-'}) [#{(r['id'])}]"


def musteri_sozluk(db):
    return {musteri_etiket(r): r["id"] for r in db.listele("SELECT * FROM musteriler ORDER BY firma, yetkili")}


def teklif_toplam(db, teklif_id):
    rows = db.listele("SELECT adet, fiyat FROM teklif_kalem WHERE teklif_id=?", (teklif_id,))
    ara = sum((r["adet"] or 0) * (r["fiyat"] or 0) for r in rows)
    oran = db.listele("SELECT kdv_oran FROM teklifler WHERE id=?", (teklif_id,))
    oran = (oran[0]["kdv_oran"] if oran else 20) or 0
    kdv = round(ara * oran / 100, 2)
    return round(ara, 2), kdv, round(ara + kdv, 2)


def teklif_no_uret(db):
    yil = date.today().year
    n = db.listele("SELECT COUNT(*) s FROM teklifler WHERE substr(tarih,1,4)=?", (str(yil),))[0]["s"]
    return f"T-{yil}-{(n + 1):04d}"


def agirlikli_ciro(db):
    rows = db.listele("SELECT tutar, olasilik FROM firsatlar WHERE asama NOT IN ('Kazanıldı','Kaybedildi')")
    return sum((r["tutar"] or 0) * (r["olasilik"] if r["olasilik"] is not None else 10) / 100 for r in rows)


def vade_yakin_mi(tarih):
    if not tarih:
        return ""
    try:
        gun = (date.fromisoformat(tarih) - date.today()).days
    except ValueError:
        return ""
    if gun < 0:
        return "gecmis"
    if gun <= 3:
        return "yakin"
    return ""


def csv_yaz(klasor, ad, basliklar, satirlar):
    import csv
    import os
    yol = os.path.join(klasor, ad)
    with open(yol, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    return yol
