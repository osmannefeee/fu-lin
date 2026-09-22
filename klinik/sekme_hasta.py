# -*- coding: utf-8 -*-
"""👥 Hastalar: kayıt, arama, borç rozeti, tedavi/şema geçişleri."""
import tkinter as tk
from tkinter import messagebox, ttk

from .tema import cift_tag, tablo_kur
from .yardim import hasta_borc, para_fmt


class SekmeHasta(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        arama = ttk.Frame(self)
        arama.pack(fill="x", pady=4)
        ttk.Label(arama, text="🔍 Ara (ad / telefon / TC):").pack(side="left")
        self.q = ttk.Entry(arama, width=40)
        self.q.pack(side="left", padx=6)
        self.q.bind("<KeyRelease>", lambda e: self.yenile())
        ttk.Button(arama, text="🦷 Şema Aç", command=self.sema_ac).pack(side="right", padx=4)
        ttk.Button(arama, text="Tedavi/Ödeme Aç", command=self.tedavi_ac).pack(side="right", padx=4)
        ttk.Button(arama, text="Sil", command=self.sil).pack(side="right", padx=4)
        ttk.Button(arama, text="Düzenle", command=self.duzenle).pack(side="right", padx=4)
        ttk.Button(arama, text="+ Yeni Hasta", command=self.form).pack(side="right", padx=4)
        self.tree = tablo_kur(self, [("id", "ID", 50), ("ad", "Ad Soyad", 200), ("tc", "TC", 110),
                                     ("tel", "Telefon", 120), ("dogum", "Doğum", 100), ("borc", "Borç", 120)])
        self.tree.bind("<Double-1>", lambda e: self.duzenle())

    def secili_id(self):
        s = self.tree.selection()
        return self.tree.item(s[0])["values"][0] if s else None

    def yenile(self):
        db = self.app.db
        q = (self.q.get() or "").strip()
        for i in self.tree.get_children():
            self.tree.delete(i)
        if q:
            rows = db.listele("""SELECT * FROM hastalar
                WHERE ad_soyad LIKE ? OR telefon LIKE ? OR tc LIKE ? ORDER BY ad_soyad""",
                              (f"%{q}%", f"%{q}%", f"%{q}%"))
        else:
            rows = db.listele("SELECT * FROM hastalar ORDER BY ad_soyad LIMIT 500")
        for i, h in enumerate(rows):
            kalan, _, _ = hasta_borc(db, h["id"])
            tag = ("kritik",) if kalan > 0.5 else cift_tag(i)
            self.tree.insert("", "end", values=(h["id"], h["ad_soyad"], h["tc"], h["telefon"],
                                                h["dogum"], para_fmt(kalan)), tags=tag)

    def form(self, kayit=None):
        win = tk.Toplevel(self)
        win.title("Hasta Kaydı")
        win.geometry("480x560")
        alanlar = {}

        def satir(etiket, key, val=""):
            ttk.Label(win, text=etiket).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(win, width=50)
            e.pack(padx=12, fill="x")
            e.insert(0, val or "")
            alanlar[key] = e

        satir("Ad Soyad *", "ad_soyad", kayit["ad_soyad"] if kayit else "")
        satir("TC Kimlik", "tc", kayit["tc"] if kayit else "")
        satir("Telefon", "telefon", kayit["telefon"] if kayit else "")
        satir("Doğum Tarihi (YYYY-AA-GG)", "dogum", kayit["dogum"] if kayit else "")
        satir("Cinsiyet", "cinsiyet", kayit["cinsiyet"] if kayit else "")
        satir("Adres", "adres", kayit["adres"] if kayit else "")
        satir("Alerji", "alerji", kayit["alerji"] if kayit else "")
        satir("Kronik Hastalık", "kronik", kayit["kronik"] if kayit else "")
        ttk.Label(win, text="Notlar").pack(anchor="w", padx=12, pady=(6, 0))
        txt = tk.Text(win, height=4)
        txt.pack(padx=12, fill="x")
        if kayit and kayit["notlar"]:
            txt.insert("1.0", kayit["notlar"])

        def kaydet():
            if not alanlar["ad_soyad"].get().strip():
                messagebox.showwarning("Uyarı", "Ad Soyad zorunludur.", parent=win)
                return
            v = {k: e.get().strip() for k, e in alanlar.items()}
            notlar = txt.get("1.0", "end").strip()
            try:
                if kayit:
                    self.app.db.sorgu("""UPDATE hastalar SET ad_soyad=?, tc=?, telefon=?, dogum=?,
                        cinsiyet=?, adres=?, alerji=?, kronik=?, notlar=? WHERE id=?""",
                        (v["ad_soyad"], v["tc"], v["telefon"], v["dogum"], v["cinsiyet"],
                         v["adres"], v["alerji"], v["kronik"], notlar, kayit["id"]))
                else:
                    self.app.db.sorgu("""INSERT INTO hastalar
                        (ad_soyad, tc, telefon, dogum, cinsiyet, adres, alerji, kronik, notlar)
                        VALUES(?,?,?,?,?,?,?,?,?)""",
                        (v["ad_soyad"], v["tc"], v["telefon"], v["dogum"], v["cinsiyet"],
                         v["adres"], v["alerji"], v["kronik"], notlar))
            except Exception as e:
                messagebox.showerror("Hata", f"Kayıt yazılamadı:\n{e}", parent=win)
                return
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=12)

    def duzenle(self):
        hid = self.secili_id()
        if not hid:
            messagebox.showinfo("Bilgi", "Önce bir hasta seçin.")
            return
        self.form(self.app.db.listele("SELECT * FROM hastalar WHERE id=?", (hid,))[0])

    def sil(self):
        hid = self.secili_id()
        if not hid:
            return
        if self.app.kullanici.get("rol") not in ("admin", "sekreter"):
            messagebox.showwarning("Yetki", "Silme yetkiniz yok.")
            return
        if messagebox.askyesno("Onay", "Hasta ve tüm kayıtları silinsin mi?"):
            db = self.app.db
            for tablo in ("odemeler", "tedaviler", "randevular", "dis_durum"):
                db.sorgu(f"DELETE FROM {tablo} WHERE hasta_id=?", (hid,))
            db.sorgu("DELETE FROM hastalar WHERE id=?", (hid,))
            self.app.yenile_hepsi()

    def tedavi_ac(self):
        hid = self.secili_id()
        if not hid:
            messagebox.showinfo("Bilgi", "Önce bir hasta seçin.")
            return
        self.app.tedavi_ac(hid)

    def sema_ac(self):
        hid = self.secili_id()
        if not hid:
            messagebox.showinfo("Bilgi", "Önce bir hasta seçin.")
            return
        self.app.sema_ac(hid)
