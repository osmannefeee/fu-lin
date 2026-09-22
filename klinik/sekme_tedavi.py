# -*- coding: utf-8 -*-
"""💳 Tedavi & Ödeme."""
import tkinter as tk
from tkinter import messagebox, ttk

from .sabitler import TEDAVI_DURUM, TEDAVI_FIYAT, ODEME_YONTEM
from .tema import cift_tag, tablo_kur
from .yardim import bugun_str, hasta_borc, hasta_sec_dict, hekim_sec_dict, para_fmt


class SekmeTedavi(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        ust = ttk.Frame(self)
        ust.pack(fill="x", pady=4)
        ttk.Label(ust, text="Hasta:").pack(side="left")
        self.cb = ttk.Combobox(ust, width=42)
        self.cb.pack(side="left", padx=6)
        self.cb.bind("<<ComboboxSelected>>", lambda e: self.yenile())
        ttk.Button(ust, text="Getir", command=self.yenile).pack(side="left")
        self.ozet = ttk.Label(ust, text="", font=("Segoe UI", 10, "bold"))
        self.ozet.pack(side="left", padx=16)
        ttk.Button(ust, text="+ Tedavi Ekle", command=lambda: self.tedavi_ekle()).pack(side="right", padx=4)
        ttk.Button(ust, text="+ Ödeme Al", command=self.odeme_ekle).pack(side="right", padx=4)
        orta = ttk.Frame(self)
        orta.pack(fill="both", expand=True)
        sol = ttk.LabelFrame(orta, text="💊 Tedaviler", padding=4)
        sol.pack(side="left", fill="both", expand=True, padx=2)
        sag = ttk.LabelFrame(orta, text="💰 Ödemeler", padding=4)
        sag.pack(side="left", fill="both", expand=True, padx=2)
        self.t_ted = tablo_kur(sol, [("id", "ID", 40), ("tarih", "Tarih", 90), ("islem", "İşlem", 180),
                                     ("dis", "Diş", 60), ("tutar", "Tutar", 100), ("durum", "Durum", 90)])
        ttk.Button(sol, text="Tedavi Sil / Durum", command=self.tedavi_islem).pack(pady=4)
        self.t_ode = tablo_kur(sag, [("id", "ID", 40), ("tarih", "Tarih", 90), ("tutar", "Tutar", 100),
                                     ("yontem", "Yöntem", 110), ("acik", "Açıklama", 170)])
        ttk.Button(sag, text="Ödeme Sil", command=self.odeme_sil).pack(pady=4)
        self.harita = {}

    def hasta_sec(self, hasta_id):
        self.harita = hasta_sec_dict(self.app.db)
        self.cb["values"] = list(self.harita.keys())
        for ad, hid in self.harita.items():
            if hid == hasta_id:
                self.cb.set(ad)
                self.app.secili_hasta = hid
                break
        self.yenile()

    def secili_hasta(self):
        if not self.harita:
            self.harita = hasta_sec_dict(self.app.db)
            self.cb["values"] = list(self.harita.keys())
        return self.harita.get(self.cb.get(), self.app.secili_hasta)

    def yenile(self):
        db = self.app.db
        self.harita = hasta_sec_dict(db)
        self.cb["values"] = list(self.harita.keys())
        hid = self.secili_hasta()
        for i in self.t_ted.get_children():
            self.t_ted.delete(i)
        for i in self.t_ode.get_children():
            self.t_ode.delete(i)
        if not hid:
            self.ozet.config(text="Hasta seçin")
            return
        self.app.secili_hasta = hid
        kalan, toplam, odenen = hasta_borc(db, hid)
        self.ozet.config(text=f"Toplam: {para_fmt(toplam)}  |  Ödenen: {para_fmt(odenen)}  |  Kalan: {para_fmt(kalan)}")
        for i, r in enumerate(db.listele("SELECT * FROM tedaviler WHERE hasta_id=? ORDER BY tarih DESC", (hid,))):
            self.t_ted.insert("", "end", values=(r["id"], r["tarih"], r["islem"], r["dis_no"],
                                                 para_fmt(r["toplam_ucret"]), r["durum"]), tags=cift_tag(i))
        for i, r in enumerate(db.listele("SELECT * FROM odemeler WHERE hasta_id=? ORDER BY tarih DESC", (hid,))):
            self.t_ode.insert("", "end", values=(r["id"], r["tarih"], para_fmt(r["tutar"]),
                                                 r["yontem"], r["aciklama"]), tags=cift_tag(i))

    def tedavi_ekle(self, dis_no=""):
        db = self.app.db
        hid = self.secili_hasta()
        if not hid:
            messagebox.showinfo("Bilgi", "Önce hasta seçin.")
            return
        hekimler = hekim_sec_dict(db)
        win = tk.Toplevel(self)
        win.title("Tedavi Ekle")
        win.geometry("430x520")
        ttk.Label(win, text="İşlem").pack(anchor="w", padx=12, pady=(8, 0))
        cb_islem = ttk.Combobox(win, values=list(TEDAVI_FIYAT.keys()))
        cb_islem.pack(padx=12, fill="x")
        cb_islem.set("Dolgu")
        ttk.Label(win, text="Hekim").pack(anchor="w", padx=12, pady=(8, 0))
        cb_he = ttk.Combobox(win, values=list(hekimler.keys()))
        cb_he.pack(padx=12, fill="x")
        if hekimler:
            cb_he.set(list(hekimler.keys())[0])
        ttk.Label(win, text="Tarih (YYYY-AA-GG)").pack(anchor="w", padx=12, pady=(8, 0))
        e_t = ttk.Entry(win)
        e_t.pack(padx=12, fill="x")
        e_t.insert(0, bugun_str())
        ttk.Label(win, text="Diş No (örn. 16, 36)").pack(anchor="w", padx=12, pady=(8, 0))
        e_d = ttk.Entry(win)
        e_d.pack(padx=12, fill="x")
        e_d.insert(0, dis_no)
        fr = ttk.Frame(win)
        fr.pack(fill="x", padx=12, pady=6)
        ttk.Label(fr, text="Adet:").pack(side="left")
        e_a = ttk.Entry(fr, width=8)
        e_a.pack(side="left", padx=4)
        e_a.insert(0, "1")
        ttk.Label(fr, text="Birim Ücret:").pack(side="left", padx=(10, 0))
        e_u = ttk.Entry(fr, width=14)
        e_u.pack(side="left", padx=4)
        e_u.insert(0, str(TEDAVI_FIYAT.get("Dolgu", 0)))
        cb_islem.bind("<<ComboboxSelected>>",
                      lambda e: (e_u.delete(0, "end"), e_u.insert(0, str(TEDAVI_FIYAT.get(cb_islem.get(), 0)))))
        ttk.Label(win, text="Durum").pack(anchor="w", padx=12, pady=(8, 0))
        cb_d = ttk.Combobox(win, values=TEDAVI_DURUM)
        cb_d.pack(padx=12, fill="x")
        cb_d.set("Tamamlandı")
        ttk.Label(win, text="Not").pack(anchor="w", padx=12, pady=(8, 0))
        e_n = ttk.Entry(win)
        e_n.pack(padx=12, fill="x")

        def kaydet():
            try:
                adet = int(e_a.get() or 1)
                birim = float(e_u.get() or 0)
            except ValueError:
                messagebox.showwarning("Uyarı", "Adet / ücret sayısal olmalı.", parent=win)
                return
            db.sorgu("""INSERT INTO tedaviler
                (hasta_id, hekim_id, tarih, dis_no, islem, adet, birim_ucret, toplam_ucret, durum, notlar)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (hid, hekimler.get(cb_he.get()), e_t.get().strip(), e_d.get().strip(), cb_islem.get(),
                 adet, birim, adet * birim, cb_d.get(), e_n.get().strip()))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=12)

    def tedavi_islem(self):
        s = self.t_ted.selection()
        if not s:
            return
        tid = self.t_ted.item(s[0])["values"][0]
        win = tk.Toplevel(self)
        win.title("Tedavi İşlem")
        win.geometry("280x200")
        ttk.Label(win, text="Durum:").pack(pady=6)
        cb = ttk.Combobox(win, values=TEDAVI_DURUM)
        cb.pack(padx=12, fill="x")
        cb.set("Tamamlandı")

        def uygula():
            self.app.db.sorgu("UPDATE tedaviler SET durum=? WHERE id=?", (cb.get(), tid))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Güncelle", command=uygula).pack(pady=8)
        ttk.Button(win, text="Tedaviyi Sil",
                   command=lambda: (self.app.db.sorgu("DELETE FROM tedaviler WHERE id=?", (tid,)),
                                    win.destroy(), self.app.yenile_hepsi())).pack()

    def odeme_ekle(self):
        db = self.app.db
        hid = self.secili_hasta()
        if not hid:
            messagebox.showinfo("Bilgi", "Önce hasta seçin.")
            return
        kalan, _, _ = hasta_borc(db, hid)
        win = tk.Toplevel(self)
        win.title("Ödeme Al")
        win.geometry("380x360")
        ttk.Label(win, text=f"Kalan borç: {para_fmt(kalan)}").pack(pady=6)
        ttk.Label(win, text="Tutar *").pack(anchor="w", padx=12)
        e_tutar = ttk.Entry(win)
        e_tutar.pack(padx=12, fill="x")
        e_tutar.insert(0, str(int(kalan)) if kalan > 0 else "")
        ttk.Label(win, text="Tarih (YYYY-AA-GG)").pack(anchor="w", padx=12, pady=(8, 0))
        e_t = ttk.Entry(win)
        e_t.pack(padx=12, fill="x")
        e_t.insert(0, bugun_str())
        ttk.Label(win, text="Yöntem").pack(anchor="w", padx=12, pady=(8, 0))
        cb = ttk.Combobox(win, values=ODEME_YONTEM)
        cb.pack(padx=12, fill="x")
        cb.set("Nakit")
        ttk.Label(win, text="Açıklama").pack(anchor="w", padx=12, pady=(8, 0))
        e_a = ttk.Entry(win)
        e_a.pack(padx=12, fill="x")

        def kaydet():
            try:
                tutar = float(e_tutar.get())
                if tutar <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli tutar girin.", parent=win)
                return
            db.sorgu("INSERT INTO odemeler(hasta_id, tarih, tutar, yontem, aciklama) VALUES(?,?,?,?,?)",
                     (hid, e_t.get().strip(), tutar, cb.get(), e_a.get().strip()))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Ödemeyi Kaydet", command=kaydet).pack(pady=12)

    def odeme_sil(self):
        if self.app.kullanici.get("rol") not in ("admin", "sekreter"):
            messagebox.showwarning("Yetki", "Silme yetkiniz yok.")
            return
        s = self.t_ode.selection()
        if s and messagebox.askyesno("Onay", "Ödeme silinsin mi?"):
            self.app.db.sorgu("DELETE FROM odemeler WHERE id=?", (self.t_ode.item(s[0])["values"][0],))
            self.app.yenile_hepsi()
