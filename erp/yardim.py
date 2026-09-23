# -*- coding: utf-8 -*-
from datetime import date

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


def cari_etiket(r):
    return f"{r['unvan']} [{r['tip']}] (#{r['id']})"


def cari_sozluk(db, tip=None):
    sql = "SELECT * FROM cariler ORDER BY unvan"
    rows = db.listele(sql if not tip else sql.replace("ORDER", "WHERE tip=? ORDER"), (tip,) if tip else ())
    return {cari_etiket(r): r["id"] for r in rows}


def cari_bakiye(db, cari_id):
    """Pozitif = bizden alacaklılar (müşteri borcu) / negatif = bizim borcumuz."""
    tip = db.listele("SELECT tip FROM cariler WHERE id=?", (cari_id,))[0]["tip"]
    if tip == "Müşteri":
        sat = db.listele("SELECT COALESCE(SUM(genel),0) s FROM faturalar WHERE tip='Satış' AND cari_id=?",
                         (cari_id,))[0]["s"] or 0
        tah = db.listele("""SELECT COALESCE(SUM(tutar),0) s FROM kasa_hareket
                            WHERE yon='Giriş' AND cari_id=?""", (cari_id,))[0]["s"] or 0
        return sat - tah
    als = db.listele("SELECT COALESCE(SUM(genel),0) s FROM faturalar WHERE tip='Alış' AND cari_id=?",
                     (cari_id,))[0]["s"] or 0
    ode = db.listele("""SELECT COALESCE(SUM(tutar),0) s FROM kasa_hareket
                        WHERE yon='Çıkış' AND cari_id=?""", (cari_id,))[0]["s"] or 0
    return ode - als  # negatif = tedarikçiye borcumuz


def stok_degeri(db):
    r = db.listele("SELECT COALESCE(SUM(miktar*alis_fiyat),0) s FROM urunler")[0]["s"]
    return r or 0


def fatura_no_uret(db, tip):
    yil = date.today().year
    harf = "S" if tip == "Satış" else "A"
    n = db.listele("SELECT COUNT(*) s FROM faturalar WHERE tip=? AND substr(tarih,1,4)=?",
                   (tip, str(yil)))[0]["s"]
    return f"{harf}-{yil}-{(n + 1):04d}"


def csv_yaz(klasor, ad, basliklar, satirlar):
    import csv
    import os
    yol = os.path.join(klasor, ad)
    with open(yol, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    return yol
