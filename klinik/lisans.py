# -*- coding: utf-8 -*-
"""14 günlük deneme + kurulum-kodlu lisans."""
import hashlib
import tkinter as tk
import urllib.parse
import webbrowser
from datetime import date, datetime
from tkinter import messagebox, ttk

from .sabitler import DENEME_GUN, LISANS_SECRET, LISANS_TEL, TARIH_FMT, WA_NO
from .yardim import ayar_get, ayar_set


def kurulum_kodu_get(db):
    kod = ayar_get(db, "kurulum_kodu")
    if not kod:
        import uuid
        kod = uuid.uuid4().hex[:8].upper()
        ayar_set(db, "kurulum_kodu", kod)
    return kod


def lisans_anahtari_uret(kod):
    ham = f"{LISANS_SECRET}|{(kod or '').strip().upper()}|TAM"
    h = hashlib.sha256(ham.encode("utf-8")).hexdigest().upper()[:12]
    return f"{h[:4]}-{h[4:8]}-{h[8:12]}"


def lisans_durumu(db):
    if (ayar_get(db, "lisans_tipi") == "tam"
            and ayar_get(db, "lisans_anahtar") == lisans_anahtari_uret(ayar_get(db, "lisans_musteri"))):
        return {"tip": "tam", "kalan": None, "kilitli": False, "mesaj": "Tam lisans aktif"}
    bugun = date.today()
    ilk = ayar_get(db, "kurulum_tarihi")
    if not ilk:
        ayar_set(db, "kurulum_tarihi", bugun.strftime(TARIH_FMT))
        return {"tip": "deneme", "kalan": DENEME_GUN, "kilitli": False, "mesaj": ""}
    try:
        gecen = (bugun - datetime.strptime(ilk, TARIH_FMT).date()).days
    except ValueError:
        return {"tip": "deneme", "kalan": 0, "kilitli": True,
                "mesaj": f"Lisans kaydı bozuk. Destek: {LISANS_TEL}"}
    if gecen < 0:
        return {"tip": "deneme", "kalan": 0, "kilitli": True,
                "mesaj": f"Sistem saati geri alınmış görünüyor. Destek: {LISANS_TEL}"}
    kalan = DENEME_GUN - gecen
    if kalan <= 0:
        return {"tip": "deneme", "kalan": 0, "kilitli": True,
                "mesaj": f"14 günlük deneme süreniz doldu.\nSatın almak için: {LISANS_TEL}"}
    return {"tip": "deneme", "kalan": kalan, "kilitli": False, "mesaj": ""}


def lisans_aktivasyon_formu(parent, db):
    kod = kurulum_kodu_get(db)
    cer = ttk.Frame(parent, padding=10)
    cer.pack(fill="x")
    ttk.Label(cer, text="Kurulum kodunuz (değişmez):").pack(anchor="w")
    e_kod = ttk.Entry(cer)
    e_kod.pack(fill="x")
    e_kod.insert(0, kod)
    e_kod.config(state="readonly")
    ttk.Label(cer, text="Lisans anahtarı (satıcıdan aldığınız):").pack(anchor="w", pady=(8, 0))
    e_key = ttk.Entry(cer)
    e_key.pack(fill="x")

    def dene():
        if e_key.get().strip().upper() == lisans_anahtari_uret(kod):
            ayar_set(db, "lisans_musteri", kod)
            ayar_set(db, "lisans_anahtar", e_key.get().strip().upper())
            ayar_set(db, "lisans_tipi", "tam")
            messagebox.showinfo("Lisans", "Tam lisans etkinleştirildi. 🎉", parent=parent)
        else:
            messagebox.showwarning("Lisans", "Anahtar bu kurulum koduna ait değil.", parent=parent)

    ttk.Button(cer, text="Etkinleştir", command=dene).pack(pady=10, fill="x")

    def wa_gonder():
        msg = urllib.parse.quote(f"Merhaba, lisans almak istiyorum. Kurulum kodum: {kod}")
        webbrowser.open(f"https://wa.me/{WA_NO}?text={msg}")

    ttk.Button(cer, text="📩 Kodu WhatsApp ile Gönder", command=wa_gonder).pack(fill="x")


def kilit_penceresi(db, durum):
    sonuc = {}
    root = tk.Tk()
    root.title("Fu-Lin — Lisans")
    root.geometry("420x430")
    root.resizable(False, False)
    root.configure(bg="#0f172a")
    tk.Label(root, text="🔒", font=("Segoe UI", 36), bg="#0f172a").pack(pady=(16, 0))
    tk.Label(root, text=durum["mesaj"], font=("Segoe UI", 11, "bold"),
             bg="#0f172a", fg="white", justify="center").pack(padx=20, pady=8)
    lisans_aktivasyon_formu(root, db)

    def gir():
        if not lisans_durumu(db)["kilitli"]:
            sonuc["ok"] = True
            root.destroy()
        else:
            messagebox.showwarning("Lisans", "Lisans etkin değil.", parent=root)

    ttk.Button(root, text="Programa Gir", command=gir).pack(fill="x", padx=10)
    ttk.Button(root, text="Kapat", command=root.destroy).pack(fill="x", padx=10, pady=6)
    root.mainloop()
    return sonuc.get("ok", False)
