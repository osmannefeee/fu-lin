# Fu-Lin satıcı paneli (sende kalır, müşteriye verilmez)
# Kullanim: python lisans_panel.py
# Müşteri kurulum kodunu WhatsApp'tan gönderir -> buraya yapıştır -> anahtarı alıp müşteriye yolla.
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.parse
import webbrowser

sys.path.insert(0, '.')
from klinik.lisans import lisans_anahtari_uret

root = tk.Tk()
root.title("Fu-Lin — Lisans Paneli")
root.geometry("440x380")
root.resizable(False, False)

ttk.Label(root, text="Müşterinin kurulum kodu:").pack(anchor="w", padx=12, pady=(12, 0))
e_kod = ttk.Entry(root, font=("Consolas", 12))
e_kod.pack(padx=12, fill="x")

ttk.Label(root, text="Müşteri telefonu (05__ ___ __ __):").pack(anchor="w", padx=12, pady=(8, 0))
e_tel = ttk.Entry(root)
e_tel.pack(padx=12, fill="x")

sonuc = tk.Label(root, text="", font=("Consolas", 16, "bold"), fg="#059669")
sonuc.pack(pady=12)

anahtar = {"k": ""}

def uret():
    kod = e_kod.get().strip().upper()
    if not kod:
        messagebox.showwarning("Uyarı", "Kurulum kodu girin.", parent=root)
        return
    anahtar["k"] = lisans_anahtari_uret(kod)
    sonuc.config(text=anahtar["k"])
    root.clipboard_clear()
    root.clipboard_append(anahtar["k"])

def wa_gonder():
    if not anahtar["k"]:
        uret()
    tel = "".join(ch for ch in e_tel.get() if ch.isdigit()).lstrip("0")
    if len(tel) == 10:
        tel = "90" + tel
    if len(tel) != 12:
        messagebox.showwarning("Uyarı", "Müşteri telefonunu girin.", parent=root)
        return
    msg = urllib.parse.quote(f"Merhaba, Fu-Lin lisans anahtarınız: {anahtar['k']}\nProgramda Lisans bölümüne yapıştırıp Etkinleştir'e basın.")
    webbrowser.open(f"https://wa.me/{tel}?text={msg}")

ttk.Button(root, text="🔑 Anahtarı Üret + Kopyala", command=uret).pack(padx=12, fill="x", pady=4)
ttk.Button(root, text="📩 Müşteriye WhatsApp ile Gönder", command=wa_gonder).pack(padx=12, fill="x", pady=4)
tk.Label(root, text="Akış: müşteri kod yollar → anahtar üret → tek tıkla müşteriye gider.",
         font=("Segoe UI", 9), fg="gray").pack(pady=10)

root.mainloop()
