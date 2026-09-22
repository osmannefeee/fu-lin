# -*- coding: utf-8 -*-
"""🩺 Hekimler."""
import tkinter as tk
from tkinter import messagebox, ttk

from .tema import cift_tag, tablo_kur


class SekmeHekim(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        ust = ttk.Frame(self)
        ust.pack(fill="x", pady=4)
        ttk.Button(ust, text="+ Hekim Ekle", command=self.form).pack(side="right", padx=4)
        ttk.Button(ust, text="Düzenle", command=self.duzenle).pack(side="right", padx=4)
        ttk.Button(ust, text="Aktif/Pasif", command=self.degistir).pack(side="right", padx=4)
        self.tree = tablo_kur(self, [("id", "ID", 50), ("ad", "Ad Soyad", 220), ("brans", "Branş", 200),
                                     ("tel", "Telefon", 140), ("durum", "Durum", 100)])

    def yenile(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for i, r in enumerate(self.app.db.listele("SELECT * FROM hekimler ORDER BY ad_soyad")):
            tag = cift_tag(i) if r["aktif"] else ("kritik",)
            self.tree.insert("", "end", values=(r["id"], r["ad_soyad"], r["brans"], r["telefon"],
                                                "✅ Aktif" if r["aktif"] else "⛔ Pasif"), tags=tag)

    def secili(self):
        s = self.tree.selection()
        if not s:
            return None
        hid = self.tree.item(s[0])["values"][0]
        return self.app.db.listele("SELECT * FROM hekimler WHERE id=?", (hid,))[0]

    def form(self, kayit=None):
        win = tk.Toplevel(self)
        win.title("Hekim")
        win.geometry("380x300")
        ttk.Label(win, text="Ad Soyad *").pack(anchor="w", padx=12, pady=(8, 0))
        e_a = ttk.Entry(win)
        e_a.pack(padx=12, fill="x")
        ttk.Label(win, text="Branş").pack(anchor="w", padx=12, pady=(8, 0))
        e_b = ttk.Entry(win)
        e_b.pack(padx=12, fill="x")
        ttk.Label(win, text="Telefon").pack(anchor="w", padx=12, pady=(8, 0))
        e_t = ttk.Entry(win)
        e_t.pack(padx=12, fill="x")
        if kayit:
            e_a.insert(0, kayit["ad_soyad"] or "")
            e_b.insert(0, kayit["brans"] or "")
            e_t.insert(0, kayit["telefon"] or "")

        def kaydet():
            if not e_a.get().strip():
                messagebox.showwarning("Uyarı", "Ad Soyad zorunlu.", parent=win)
                return
            db = self.app.db
            if kayit:
                db.sorgu("UPDATE hekimler SET ad_soyad=?, brans=?, telefon=? WHERE id=?",
                         (e_a.get().strip(), e_b.get().strip(), e_t.get().strip(), kayit["id"]))
            else:
                db.sorgu("INSERT INTO hekimler(ad_soyad, brans, telefon) VALUES(?,?,?)",
                         (e_a.get().strip(), e_b.get().strip(), e_t.get().strip()))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=12)

    def duzenle(self):
        k = self.secili()
        if k:
            self.form(k)

    def degistir(self):
        k = self.secili()
        if k:
            self.app.db.sorgu("UPDATE hekimler SET aktif=? WHERE id=?",
                              (0 if k["aktif"] else 1, k["id"]))
            self.app.yenile_hepsi()
