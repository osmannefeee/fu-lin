# -*- coding: utf-8 -*-
"""Kullanıcı yönetimi (sadece admin açar)."""
import tkinter as tk
from tkinter import messagebox
from .modern import ttk

from .sabitler import ROLLER
from .yardim import sifre_hashla


def kullanici_yonetimi(pencere, db):
    import sqlite3
    win = ttk.Toplevel(pencere)
    win.title("Kullanıcı Yönetimi")
    win.geometry("620x400")
    tree = ttk.Treeview(win, columns=("id", "kadi", "ad", "rol", "durum"), show="headings")
    for k, b, w in [("id", "ID", 45), ("kadi", "Kullanıcı Adı", 140), ("ad", "Ad Soyad", 180),
                    ("rol", "Rol", 100), ("durum", "Durum", 80)]:
        tree.heading(k, text=b)
        tree.column(k, width=w)
    tree.pack(fill="both", expand=True, padx=10, pady=8)

    def listele():
        for i in tree.get_children():
            tree.delete(i)
        for r in db.listele("SELECT * FROM kullanicilar ORDER BY kullanici_adi"):
            tree.insert("", "end", values=(r["id"], r["kullanici_adi"], r["ad_soyad"], r["rol"],
                                           "Aktif" if r["aktif"] else "Pasif"))

    def form(kayit=None):
        f = ttk.Toplevel(win)
        f.title("Kullanıcı")
        f.geometry("360x340")
        ttk.Label(f, text="Kullanıcı adı *").pack(anchor="w", padx=12, pady=(8, 0))
        e_k = ttk.Entry(f)
        e_k.pack(padx=12, fill="x")
        ttk.Label(f, text="Ad Soyad").pack(anchor="w", padx=12, pady=(8, 0))
        e_a = ttk.Entry(f)
        e_a.pack(padx=12, fill="x")
        ttk.Label(f, text="Rol").pack(anchor="w", padx=12, pady=(8, 0))
        cb = ttk.Combobox(f, values=ROLLER)
        cb.pack(padx=12, fill="x")
        cb.set("personel")
        ttk.Label(f, text="Şifre (boş=bırak)").pack(anchor="w", padx=12, pady=(8, 0))
        e_s = ttk.Entry(f, show="•")
        e_s.pack(padx=12, fill="x")
        if kayit:
            e_k.insert(0, kayit["kullanici_adi"])
            e_k.configure(state="disabled")
            e_a.insert(0, kayit["ad_soyad"] or "")
            cb.set(kayit["rol"])

        def kaydet():
            ka = (kayit["kullanici_adi"] if kayit else e_k.get().strip())
            if not ka:
                messagebox.showwarning("Uyarı", "Kullanıcı adı zorunlu.", parent=f)
                return
            if kayit:
                if e_s.get():
                    db.sorgu("UPDATE kullanicilar SET ad_soyad=?, rol=?, sifre_hash=? WHERE id=?",
                             (e_a.get().strip(), cb.get(), sifre_hashla(e_s.get()), kayit["id"]))
                else:
                    db.sorgu("UPDATE kullanicilar SET ad_soyad=?, rol=? WHERE id=?",
                             (e_a.get().strip(), cb.get(), kayit["id"]))
            else:
                if not e_s.get():
                    messagebox.showwarning("Uyarı", "Şifre zorunlu.", parent=f)
                    return
                try:
                    db.sorgu("INSERT INTO kullanicilar(kullanici_adi, sifre_hash, rol, ad_soyad) VALUES(?,?,?,?)",
                             (ka, sifre_hashla(e_s.get()), cb.get(), e_a.get().strip()))
                except sqlite3.IntegrityError:
                    messagebox.showwarning("Uyarı", "Bu kullanıcı adı zaten var.", parent=f)
                    return
            f.destroy()
            listele()

        ttk.Button(f, text="Kaydet", command=kaydet).pack(pady=12)

    def secili():
        s = tree.selection()
        if not s:
            return None
        hid = tree.item(s[0])["values"][0]
        return db.listele("SELECT * FROM kullanicilar WHERE id=?", (hid,))[0]

    def duzenle():
        k = secili()
        if k:
            form(k)

    def degistir():
        k = secili()
        if not k:
            return
        if k["kullanici_adi"] == "admin":
            messagebox.showwarning("Uyarı", "admin kapatılamaz.", parent=win)
            return
        db.sorgu("UPDATE kullanicilar SET aktif=? WHERE id=?", (0 if k["aktif"] else 1, k["id"]))
        listele()

    bar = ttk.Frame(win)
    bar.pack(fill="x", padx=10, pady=4)
    ttk.Button(bar, text="+ Yeni", command=lambda: form()).pack(side="right", padx=4)
    ttk.Button(bar, text="Düzenle", command=duzenle).pack(side="right", padx=4)
    ttk.Button(bar, text="Aktif/Pasif", command=degistir).pack(side="right", padx=4)
    listele()
