# -*- coding: utf-8 -*-
"""🦷 Diş şeması: 32 diş, renkli durum, tedaviye geçiş."""
import tkinter as tk
from tkinter import messagebox, ttk

from .sabitler import DIS_DURUMLARI, DISLER_ALT, DISLER_UST, DURUM_RENK
from .yardim import hasta_sec_dict


class SekmeSema(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        ust = ttk.Frame(self)
        ust.pack(fill="x", pady=4)
        ttk.Label(ust, text="🦷 Hasta:").pack(side="left")
        self.cb = ttk.Combobox(ust, width=42)
        self.cb.pack(side="left", padx=6)
        self.cb.bind("<<ComboboxSelected>>", lambda e: self.yenile())
        ttk.Button(ust, text="Getir", command=self.yenile).pack(side="left")
        self.ozet = ttk.Label(ust, text="", font=("Segoe UI", 10, "bold"))
        self.ozet.pack(side="left", padx=16)
        ttk.Button(ust, text="Tümünü Sağlam İşaretle", command=self.temizle).pack(side="right", padx=4)
        self.cerceve = ttk.Frame(self)
        self.cerceve.pack(fill="both", expand=True, pady=4)
        self.harita = {}
        alt = ttk.Frame(self)
        alt.pack(fill="x")
        tk.Label(alt, text="Lejant:", font=("Segoe UI", 9, "bold")).pack(side="left")
        for durum, renk in DURUM_RENK.items():
            tk.Label(alt, text=f" {durum} ", bg=renk, relief="solid", bd=1,
                     font=("Segoe UI", 8)).pack(side="left", padx=2)

    def hasta_sec(self, hasta_id):
        self.harita = hasta_sec_dict(self.app.db)
        self.cb["values"] = list(self.harita.keys())
        for ad, hid in self.harita.items():
            if hid == hasta_id:
                self.cb.set(ad)
                break
        self.yenile()

    def secili_hasta(self):
        if not self.harita:
            self.harita = hasta_sec_dict(self.app.db)
            self.cb["values"] = list(self.harita.keys())
        return self.harita.get(self.cb.get(), self.app.secili_hasta)

    def yenile(self):
        for w in self.cerceve.winfo_children():
            w.destroy()
        hid = self.secili_hasta()
        if not hid:
            ttk.Label(self.cerceve, text="Önce hasta seçin.").pack()
            return
        durumlar = {r["dis_no"]: r["durum"] for r in
                    self.app.db.listele("SELECT * FROM dis_durum WHERE hasta_id=?", (hid,))}
        sorunlu = sum(1 for d in durumlar.values() if d != "Sağlam")
        self.ozet.config(text=f"İşaretli diş: {len(durumlar)}  |  Sorunlu: {sorunlu}")
        for baslik, liste in [("— ÜST ÇENE —", DISLER_UST), ("— ALT ÇENE —", DISLER_ALT)]:
            ttk.Label(self.cerceve, text=baslik, style="Title.TLabel").pack(pady=(8, 2))
            satir = tk.Frame(self.cerceve, bg="#f1f5f9")
            satir.pack()
            for no in liste:
                durum = durumlar.get(no, "Sağlam")
                renk = DURUM_RENK.get(durum, "#ffffff")
                fg = "white" if durum in ("Çürük", "Çekilmiş", "Kanal") else "black"
                tk.Button(satir, text=f"{no}\n{durum[:6]}", width=7, height=3, bg=renk, fg=fg,
                          font=("Segoe UI", 9, "bold"), relief="raised", bd=2,
                          command=lambda n=no: self.dis_form(n)).pack(side="left", padx=3, pady=3)

    def dis_form(self, dis_no):
        db = self.app.db
        hid = self.secili_hasta()
        if not hid:
            return
        rows = db.listele("SELECT * FROM dis_durum WHERE hasta_id=? AND dis_no=?", (hid, dis_no))
        mevcut = rows[0] if rows else None
        win = tk.Toplevel(self)
        win.title(f"Diş {dis_no}")
        win.geometry("340x300")
        ttk.Label(win, text=f"Diş No: {dis_no}", style="Title.TLabel").pack(pady=8)
        ttk.Label(win, text="Durum:").pack(anchor="w", padx=12)
        cb = ttk.Combobox(win, values=DIS_DURUMLARI, state="readonly")
        cb.pack(padx=12, fill="x")
        cb.set(mevcut["durum"] if mevcut else "Sağlam")
        ttk.Label(win, text="Not:").pack(anchor="w", padx=12, pady=(8, 0))
        e_n = ttk.Entry(win)
        e_n.pack(padx=12, fill="x")
        if mevcut and mevcut["notlar"]:
            e_n.insert(0, mevcut["notlar"])

        def kaydet():
            db.sorgu("INSERT OR REPLACE INTO dis_durum(hasta_id, dis_no, durum, notlar) VALUES(?,?,?,?)",
                     (hid, dis_no, cb.get(), e_n.get().strip()))
            win.destroy()
            self.yenile()

        def tedaviye():
            win.destroy()
            self.app.tedavi_ac(hid, dis_no)

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=8, fill="x", padx=12)
        ttk.Button(win, text="Bu Dişe Tedavi Ekle →", command=tedaviye).pack(fill="x", padx=12)

    def temizle(self):
        hid = self.secili_hasta()
        if hid and messagebox.askyesno("Onay", "Tüm dişler Sağlam sayılsın mı?"):
            self.app.db.sorgu("DELETE FROM dis_durum WHERE hasta_id=?", (hid,))
            self.yenile()
