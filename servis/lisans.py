# -*- coding: utf-8 -*-
import hashlib
import tkinter as tk
import urllib.parse
import webbrowser
from datetime import date, datetime
from tkinter import messagebox, ttk

from .sabitler import DENEME_GUN, LISANS_SECRET, LISANS_TEL, TARIH_FMT, WA_NO
from .yardim import ayar


def kod_get(db):
    kod = ayar(db, "kurulum_kodu")
    if not kod:
        import uuid
        kod = uuid.uuid4().hex[:8].upper()
        ayar(db, "kurulum_kodu", kod)
    return kod


def anahtar_uret(kod):
    h = hashlib.sha256(f"{LISANS_SECRET}|{(kod or '').strip().upper()}|TAM".encode()).hexdigest().upper()[:12]
    return f"{h[:4]}-{h[4:8]}-{h[8:12]}"


def durum(db):
    if ayar(db, "lisans_tipi") == "tam" and ayar(db, "lisans_anahtar") == anahtar_uret(ayar(db, "lisans_musteri")):
        return {"tip": "tam", "kalan": None, "kilitli": False}
    bugun = date.today()
    ilk = ayar(db, "kurulum_tarihi")
    if not ilk:
        ayar(db, "kurulum_tarihi", bugun.strftime(TARIH_FMT))
        return {"tip": "deneme", "kalan": DENEME_GUN, "kilitli": False}
    try:
        gecen = (bugun - datetime.strptime(ilk, TARIH_FMT).date()).days
    except ValueError:
        return {"tip": "deneme", "kalan": 0, "kilitli": True}
    if gecen < 0 or DENEME_GUN - gecen <= 0:
        return {"tip": "deneme", "kalan": 0, "kilitli": True}
    return {"tip": "deneme", "kalan": DENEME_GUN - gecen, "kilitli": False}


def aktivasyon_formu(parent, db):
    kod = kod_get(db)
    cer = ttk.Frame(parent, padding=10)
    cer.pack(fill="x")
    ttk.Label(cer, text="Kurulum kodunuz:").pack(anchor="w")
    e_kod = ttk.Entry(cer)
    e_kod.pack(fill="x")
    e_kod.insert(0, kod)
    e_kod.config(state="readonly")
    ttk.Label(cer, text="Lisans anahtarı:").pack(anchor="w", pady=(8, 0))
    e_key = ttk.Entry(cer)
    e_key.pack(fill="x")

    def dene():
        if e_key.get().strip().upper() == anahtar_uret(kod):
            ayar(db, "lisans_musteri", kod)
            ayar(db, "lisans_anahtar", e_key.get().strip().upper())
            ayar(db, "lisans_tipi", "tam")
            messagebox.showinfo("Lisans", "Tam lisans aktif. 🎉", parent=parent)
        else:
            messagebox.showwarning("Lisans", "Anahtar bu koda ait değil.", parent=parent)

    ttk.Button(cer, text="Etkinleştir", command=dene).pack(pady=8, fill="x")

    def wa():
        m = urllib.parse.quote(f"Merhaba, lisans almak istiyorum. Kurulum kodum: {kod}")
        webbrowser.open(f"https://wa.me/{WA_NO}?text={m}")

    ttk.Button(cer, text="📩 Kodu WhatsApp ile Gönder", command=wa).pack(fill="x")


def kilit_goster(db):
    s = {}
    r = tk.Tk()
    r.title("Servis Takip — Lisans")
    r.geometry("400x400")
    r.configure(bg="#0b1120")
    tk.Label(r, text="🔒", font=("Segoe UI", 34), bg="#0b1120").pack(pady=(14, 0))
    tk.Label(r, text=f"14 günlük deneme doldu.\n{LISANS_TEL}", bg="#0b1120", fg="white",
             font=("Segoe UI", 11, "bold"), justify="center").pack(pady=6)
    aktivasyon_formu(r, db)

    def gir():
        if not durum(db)["kilitli"]:
            s["ok"] = True
            r.destroy()

    ttk.Button(r, text="Programa Gir", command=gir).pack(fill="x", padx=10)
    ttk.Button(r, text="Kapat", command=r.destroy).pack(fill="x", padx=10, pady=6)
    r.mainloop()
    return s.get("ok", False)
