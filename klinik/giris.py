# -*- coding: utf-8 -*-
"""Kullanıcı giriş ekranı."""
import tkinter as tk
from tkinter import messagebox, ttk

from .yardim import ayar_get, sifre_hashla


def giris_yap(db):
    sonuc = {}
    root = tk.Tk()
    root.title("🦷 Klinik Girişi")
    root.geometry("400x340")
    root.resizable(False, False)
    root.configure(bg="#0f172a")

    tk.Label(root, text="🦷", font=("Segoe UI", 40), bg="#0f172a", fg="white").pack(pady=(18, 0))
    tk.Label(root, text=ayar_get(db, "klinik_adi"), font=("Segoe UI", 12, "bold"),
             bg="#0f172a", fg="white").pack()
    tk.Label(root, text="Kullanıcı Girişi", font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8").pack(pady=(0, 10))

    cer = tk.Frame(root, bg="#0f172a")
    cer.pack(padx=30, fill="x")
    tk.Label(cer, text="Kullanıcı adı", bg="#0f172a", fg="#cbd5e1").pack(anchor="w")
    e_k = ttk.Entry(cer, width=34)
    e_k.pack(fill="x", pady=(0, 8))
    tk.Label(cer, text="Şifre", bg="#0f172a", fg="#cbd5e1").pack(anchor="w")
    e_s = ttk.Entry(cer, width=34, show="•")
    e_s.pack(fill="x")
    durum = tk.Label(root, text="Varsayılan: admin / admin123", bg="#0f172a", fg="#64748b",
                     font=("Segoe UI", 8))
    durum.pack(pady=8)

    def dene(event=None):
        rows = db.listele("SELECT * FROM kullanicilar WHERE kullanici_adi=? AND aktif=1", (e_k.get().strip(),))
        if rows and rows[0]["sifre_hash"] == sifre_hashla(e_s.get()):
            sonuc["user"] = dict(rows[0])
            root.destroy()
        else:
            durum.config(text="Hatalı kullanıcı adı veya şifre!", fg="#f87171")
            messagebox.showwarning("Giriş", "Hatalı kullanıcı adı veya şifre.", parent=root)

    ttk.Button(root, text="Giriş Yap", command=dene).pack(pady=6, ipadx=20)
    e_k.focus_set()
    root.bind("<Return>", dene)
    root.mainloop()
    return sonuc.get("user")
