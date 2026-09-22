# -*- coding: utf-8 -*-
"""Saf yardımcılar: veritabanı nesnesi parametre alır, kimseyi import etmez (sabitler hariç)."""
import hashlib
import urllib.parse
import urllib.request
from datetime import date, timedelta

from .sabitler import TARIH_FMT


def bugun_str():
    return date.today().strftime(TARIH_FMT)


def yarin_str():
    return (date.today() + timedelta(days=1)).strftime(TARIH_FMT)


def sifre_hashla(sifre):
    return hashlib.sha256((sifre or "").encode("utf-8")).hexdigest()


def para_fmt(x):
    try:
        return f"{float(x or 0):,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00 ₺"


def hasta_borc(db, hasta_id):
    top = db.listele("SELECT COALESCE(SUM(toplam_ucret),0) t FROM tedaviler WHERE hasta_id=?", (hasta_id,))
    ode = db.listele("SELECT COALESCE(SUM(tutar),0) o FROM odemeler WHERE hasta_id=?", (hasta_id,))
    toplam = (top[0]["t"] if top else 0) or 0
    odenen = (ode[0]["o"] if ode else 0) or 0
    return toplam - odenen, toplam, odenen


def ayar_get(db, anahtar, varsayilan=""):
    r = db.listele("SELECT deger FROM ayarlar WHERE anahtar=?", (anahtar,))
    return r[0]["deger"] if r else varsayilan


def ayar_set(db, anahtar, deger):
    db.sorgu("INSERT OR REPLACE INTO ayarlar(anahtar, deger) VALUES(?,?)", (anahtar, deger))


def hasta_sec_dict(db):
    rows = db.listele("SELECT id, ad_soyad, telefon FROM hastalar ORDER BY ad_soyad")
    return {f"{r['ad_soyad']} ({r['telefon'] or '-'}) [#{(r['id'])}]": r["id"] for r in rows}


def hekim_sec_dict(db):
    rows = db.listele("SELECT id, ad_soyad FROM hekimler WHERE aktif=1 ORDER BY ad_soyad")
    return {r["ad_soyad"]: r["id"] for r in rows}


def sms_metni_uret(db, hasta_adi, tarih, saat, hekim=""):
    sablon = ayar_get(db, "sms_sablon")
    klinik = ayar_get(db, "klinik_adi")
    try:
        return sablon.format(hasta=hasta_adi, tarih=tarih, saat=saat, hekim=hekim or "", klinik=klinik)
    except (KeyError, IndexError, ValueError):
        return f"Sayın {hasta_adi}, {tarih} {saat} randevunuz vardır. - {klinik}"


def netgsm_gonder(db, telefon, mesaj):
    user = ayar_get(db, "netgsm_user").strip()
    pwd = ayar_get(db, "netgsm_pass").strip()
    header = ayar_get(db, "netgsm_header").strip()
    tel = "".join(ch for ch in (telefon or "") if ch.isdigit()).lstrip("0")
    if len(tel) == 10:
        tel = "90" + tel
    if not (user and pwd and header):
        return False, "NetGSM ayarı eksik (simülasyon)"
    params = urllib.parse.urlencode({
        "usercode": user, "password": pwd, "gsmno": tel,
        "message": mesaj, "msgheader": header,
    })
    try:
        with urllib.request.urlopen("https://api.netgsm.com.tr/sms/send/get/?" + params, timeout=15) as r:
            govde = r.read().decode("utf-8", errors="ignore").strip()
        return (True, f"Gönderildi ({govde})") if govde.startswith("00") else (False, f"API hatası: {govde}")
    except Exception as e:
        return False, f"Bağlantı hatası: {e}"
