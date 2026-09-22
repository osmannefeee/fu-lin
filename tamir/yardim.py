# -*- coding: utf-8 -*-
"""Saf yardımcılar."""
from datetime import date, timedelta

from .sabitler import TARIH_FMT


def bugun():
    return date.today().strftime(TARIH_FMT)


def yarin():
    return (date.today() + timedelta(days=1)).strftime(TARIH_FMT)


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


def emir_bakiye(db, emir_id):
    top = db.listele("SELECT toplam t FROM is_emirleri WHERE id=?", (emir_id,))
    ode = db.listele("SELECT COALESCE(SUM(tutar),0) o FROM odemeler WHERE emir_id=?", (emir_id,))
    toplam = (top[0]["t"] if top else 0) or 0
    odenen = (ode[0]["o"] if ode else 0) or 0
    return toplam - odenen, toplam, odenen


def musteri_etiket(r):
    return f"{r['ad_soyad']} ({r['telefon'] or '-'}) [#{(r['id'])}]"


def musteri_sozluk(db):
    return {musteri_etiket(r): r["id"] for r in db.listele("SELECT * FROM musteriler ORDER BY ad_soyad")}


def sms_metni(db, ad, no, durum):
    try:
        return ayar(db, "sms_sablon").format(ad=ad, no=no, durum=durum, isletme=ayar(db, "isletme"))
    except (KeyError, IndexError, ValueError):
        return f"Sayın {ad}, {no} nolu kaydınız {durum} aşamasında."


def fatura_no_uret(db):
    yil = date.today().year
    r = db.listele("SELECT COUNT(*) s FROM faturalar WHERE substr(tarih,1,4)=?", (str(yil),))[0]["s"]
    return f"{yil}-{(r + 1):05d}"


def fatura_kes(db, emir_id, kdv_oran=20.0):
    """Emirden fatura oluşturur (işçilik + parça kalemleri). Varsa mevcudu döner."""
    var = db.listele("SELECT * FROM faturalar WHERE emir_id=?", (emir_id,))
    if var:
        return dict(var[0])
    emir = db.listele("SELECT * FROM is_emirleri WHERE id=?", (emir_id,))[0]
    parcalar = db.listele("SELECT * FROM emir_parca WHERE emir_id=?", (emir_id,))
    ara = (emir["iscilik"] or 0) + sum((p["adet"] or 0) * (p["fiyat"] or 0) for p in parcalar)
    kdv = round(ara * float(kdv_oran) / 100, 2)
    no = fatura_no_uret(db)
    db.sorgu("""INSERT INTO faturalar(emir_id,no,tarih,ara_toplam,kdv_oran,kdv,genel)
                VALUES(?,?,?,?,?,?,?)""",
             (emir_id, no, date.today().strftime(TARIH_FMT),
              round(ara, 2), float(kdv_oran), kdv, round(ara + kdv, 2)))
    return dict(db.listele("SELECT * FROM faturalar WHERE emir_id=?", (emir_id,))[0])


def fatura_html(isletme, musteri, emir, parcalar, fatura):
    kalem = [f"<tr><td>{emir['yapilan'] or 'Servis işçiliği'}</td><td>1</td>"
             f"<td>{emir['iscilik'] or 0:,.2f} ₺</td></tr>"]
    for p in parcalar:
        tut = (p["adet"] or 0) * (p["fiyat"] or 0)
        kalem.append(f"<tr><td>Parça: {p['urun']}</td><td>{p['adet']}</td><td>{tut:,.2f} ₺</td></tr>")
    return f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<title>Fatura {fatura['no']}</title></head>
<body style="font-family:Arial;max-width:700px;margin:30px auto;color:#111">
<h2>{isletme}</h2><p><b>Servis Faturası</b> No: {fatura['no']} &nbsp; Tarih: {fatura['tarih']}</p>
<hr><p><b>Müşteri:</b> {musteri['ad_soyad']} — {musteri['telefon'] or ''}<br>
<b>Cihaz:</b> {emir['cihaz_tur'] or ''} {emir['marka'] or ''} {emir['model'] or ''} (Emir #{emir['id']})</p>
<table border="1" cellpadding="8" cellspacing="0" width="100%">
<tr style="background:#eee"><th>İşlem</th><th>Adet</th><th>Tutar</th></tr>
{''.join(kalem)}
</table>
<p style="text-align:right">Ara toplam: {fatura['ara_toplam']:,.2f} ₺<br>
KDV (%{fatura['kdv_oran']:g}): {fatura['kdv']:,.2f} ₺<br>
<b>GENEL TOPLAM: {fatura['genel']:,.2f} ₺</b></p>
<p><small>Bu belge bilgilendirme amaçlı servis fişidir. e-Fatura entegrasyonu yakında.</small></p>
</body></html>"""


def csv_yaz(klasor, ad, basliklar, satirlar):
    import csv
    import os
    yol = os.path.join(klasor, ad)
    with open(yol, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    return yol
