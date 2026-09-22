# -*- coding: utf-8 -*-
"""📦 Stok & Gider."""
import tkinter as tk
from tkinter import messagebox, ttk

from .sabitler import GIDER_KATEGORI
from .tema import cift_tag, tablo_kur
from .yardim import bugun_str, para_fmt


class SekmeStok(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        f1 = ttk.Frame(nb, padding=6)
        f2 = ttk.Frame(nb, padding=6)
        nb.add(f1, text="  Malzeme Stoğu  ")
        nb.add(f2, text="  Giderler  ")
        ust = ttk.Frame(f1)
        ust.pack(fill="x")
        ttk.Button(ust, text="+ Malzeme", command=self.stok_form).pack(side="right", padx=4)
        ttk.Button(ust, text="Stok Giriş/Çıkış", command=self.stok_hareket).pack(side="right", padx=4)
        ttk.Button(ust, text="Sil", command=self.stok_sil).pack(side="right", padx=4)
        self.t_stok = tablo_kur(f1, [("id", "ID", 45), ("urun", "Ürün", 220), ("kat", "Kategori", 140),
                                     ("miktar", "Miktar", 90), ("birim", "Birim", 80), ("kritik", "Kritik", 80)])
        ust2 = ttk.Frame(f2)
        ust2.pack(fill="x")
        ttk.Button(ust2, text="+ Gider Ekle", command=self.gider_form).pack(side="right", padx=4)
        ttk.Button(ust2, text="Sil", command=self.gider_sil).pack(side="right", padx=4)
        self.t_gider = tablo_kur(f2, [("id", "ID", 45), ("tarih", "Tarih", 100), ("kat", "Kategori", 160),
                                      ("tutar", "Tutar", 120), ("acik", "Açıklama", 250)])

    def yenile(self):
        db = self.app.db
        for i in self.t_stok.get_children():
            self.t_stok.delete(i)
        for i, r in enumerate(db.listele("SELECT * FROM stok ORDER BY urun")):
            kritik = (r["miktar"] or 0) <= (r["kritik_seviye"] or 0)
            self.t_stok.insert("", "end", values=(r["id"], ("⚠️ " if kritik else "") + r["urun"],
                                                  r["kategori"], r["miktar"], r["birim"], r["kritik_seviye"]),
                               tags=("kritik",) if kritik else cift_tag(i))
        for i in self.t_gider.get_children():
            self.t_gider.delete(i)
        for i, r in enumerate(db.listele("SELECT * FROM giderler ORDER BY tarih DESC LIMIT 300")):
            self.t_gider.insert("", "end", values=(r["id"], r["tarih"], r["kategori"],
                                                   para_fmt(r["tutar"]), r["aciklama"]), tags=cift_tag(i))

    def stok_form(self):
        win = tk.Toplevel(self)
        win.title("Malzeme")
        win.geometry("360x340")
        alan = {}
        for et, k, v in [("Ürün adı *", "urun", ""), ("Kategori", "kat", ""), ("Miktar", "mik", "0"),
                         ("Birim", "bir", "Adet"), ("Kritik Seviye", "kri", "5")]:
            ttk.Label(win, text=et).pack(anchor="w", padx=12, pady=(8, 0))
            e = ttk.Entry(win)
            e.pack(padx=12, fill="x")
            e.insert(0, v)
            alan[k] = e

        def kaydet():
            if not alan["urun"].get().strip():
                return
            try:
                m = float(alan["mik"].get() or 0)
                kr = float(alan["kri"].get() or 5)
            except ValueError:
                messagebox.showwarning("Uyarı", "Miktar sayısal olmalı.", parent=win)
                return
            self.app.db.sorgu("""INSERT INTO stok(urun, kategori, miktar, birim, kritik_seviye, son_guncelleme)
                                 VALUES(?,?,?,?,?,?)""",
                              (alan["urun"].get().strip(), alan["kat"].get().strip(), m,
                               alan["bir"].get().strip(), kr, bugun_str()))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=10)

    def stok_hareket(self):
        s = self.t_stok.selection()
        if not s:
            messagebox.showinfo("Bilgi", "Malzeme seçin.")
            return
        sid = self.t_stok.item(s[0])["values"][0]
        win = tk.Toplevel(self)
        win.title("Stok Hareket")
        win.geometry("300x200")
        ttk.Label(win, text="Miktar (+ giriş / - çıkış):").pack(pady=8)
        e = ttk.Entry(win)
        e.pack(padx=12, fill="x")

        def uygula():
            try:
                d = float(e.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Sayısal girin.", parent=win)
                return
            self.app.db.sorgu("UPDATE stok SET miktar=miktar+?, son_guncelleme=? WHERE id=?",
                              (d, bugun_str(), sid))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Uygula", command=uygula).pack(pady=10)

    def stok_sil(self):
        s = self.t_stok.selection()
        if s and messagebox.askyesno("Onay", "Malzeme silinsin mi?"):
            self.app.db.sorgu("DELETE FROM stok WHERE id=?", (self.t_stok.item(s[0])["values"][0],))
            self.app.yenile_hepsi()

    def gider_form(self):
        win = tk.Toplevel(self)
        win.title("Gider")
        win.geometry("360x300")
        ttk.Label(win, text="Tarih (YYYY-AA-GG)").pack(anchor="w", padx=12, pady=(8, 0))
        e_t = ttk.Entry(win)
        e_t.pack(padx=12, fill="x")
        e_t.insert(0, bugun_str())
        ttk.Label(win, text="Kategori").pack(anchor="w", padx=12, pady=(8, 0))
        cb = ttk.Combobox(win, values=GIDER_KATEGORI)
        cb.pack(padx=12, fill="x")
        cb.set("Malzeme")
        ttk.Label(win, text="Tutar *").pack(anchor="w", padx=12, pady=(8, 0))
        e_tu = ttk.Entry(win)
        e_tu.pack(padx=12, fill="x")
        ttk.Label(win, text="Açıklama").pack(anchor="w", padx=12, pady=(8, 0))
        e_a = ttk.Entry(win)
        e_a.pack(padx=12, fill="x")

        def kaydet():
            try:
                tutar = float(e_tu.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Tutar sayısal olmalı.", parent=win)
                return
            self.app.db.sorgu("INSERT INTO giderler(tarih, kategori, tutar, aciklama) VALUES(?,?,?,?)",
                              (e_t.get().strip(), cb.get(), tutar, e_a.get().strip()))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=10)

    def gider_sil(self):
        s = self.t_gider.selection()
        if s and messagebox.askyesno("Onay", "Gider silinsin mi?"):
            self.app.db.sorgu("DELETE FROM giderler WHERE id=?", (self.t_gider.item(s[0])["values"][0],))
            self.app.yenile_hepsi()
