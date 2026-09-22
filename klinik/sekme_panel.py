# -*- coding: utf-8 -*-
"""📊 Panel: özet kartları + bugünkü randevular + borçlular."""
from tkinter import ttk
from datetime import date

from .sabitler import KART_RENKLERI
from .tema import cift_tag, tablo_duzeni
from .yardim import bugun_str, hasta_borc, para_fmt


class SekmePanel(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        kartlar = ttk.Frame(self)
        kartlar.pack(fill="x", pady=4)
        self.deger = {}
        for i, (anahtar, baslik) in enumerate([
                ("hasta", "👥 Toplam Hasta"), ("bugun", "📅 Bugünkü Randevu"),
                ("borc", "💰 Bekleyen Alacak"), ("aylik", "💵 Bu Ay Tahsilat")]):
            cer = ttk.Frame(kartlar, padding=12)
            cer.grid(row=0, column=i, padx=6, sticky="ew")
            kartlar.columnconfigure(i, weight=1)
            ttk.Label(cer, text=baslik, style="Title.TLabel").pack()
            v = ttk.Label(cer, text="-", font=("Segoe UI", 16, "bold"))
            v.pack()
            cer.configure(style="Card.TFrame")
            self.deger[anahtar] = v
        # kart renkleri ttk ile sınırlı; canlılık rozet tablolarda
        alt = ttk.Frame(self)
        alt.pack(fill="both", expand=True, pady=6)
        sol = ttk.LabelFrame(alt, text="📌 Bugünkü Randevular", padding=6)
        sol.pack(side="left", fill="both", expand=True, padx=4)
        sag = ttk.LabelFrame(alt, text="⚠️ Borcu Olan Hastalar (ilk 50)", padding=6)
        sag.pack(side="left", fill="both", expand=True, padx=4)
        self.t_bugun = ttk.Treeview(sol, columns=("saat", "hasta", "hekim", "islem", "durum"),
                                    show="headings", height=12)
        for k, b in [("saat", "⏰ Saat"), ("hasta", "Hasta"), ("hekim", "Hekim"),
                     ("islem", "İşlem"), ("durum", "Durum")]:
            self.t_bugun.heading(k, text=b)
            self.t_bugun.column(k, width=120)
        self.t_bugun.pack(fill="both", expand=True)
        tablo_duzeni(self.t_bugun)
        self.t_borc = ttk.Treeview(sag, columns=("hasta", "telefon", "borc"), show="headings", height=12)
        for k, b in [("hasta", "Hasta"), ("telefon", "Telefon"), ("borc", "Kalan Borç")]:
            self.t_borc.heading(k, text=b)
        self.t_borc.pack(fill="both", expand=True)
        tablo_duzeni(self.t_borc)

    def yenile(self):
        db = self.app.db
        n_hasta = db.listele("SELECT COUNT(*) s FROM hastalar")[0]["s"]
        n_bugun = db.listele("SELECT COUNT(*) s FROM randevular WHERE tarih=?", (bugun_str(),))[0]["s"]
        top = db.listele("SELECT COALESCE(SUM(toplam_ucret),0) s FROM tedaviler")[0]["s"] or 0
        ode = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler")[0]["s"] or 0
        ay = date.today().strftime("%Y-%m")
        aylik = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler WHERE substr(tarih,1,7)=?", (ay,))[0]["s"] or 0
        self.deger["hasta"].config(text=str(n_hasta))
        self.deger["bugun"].config(text=str(n_bugun))
        self.deger["borc"].config(text=para_fmt(top - ode))
        self.deger["aylik"].config(text=para_fmt(aylik))

        for i in self.t_bugun.get_children():
            self.t_bugun.delete(i)
        rows = db.listele("""SELECT r.saat, h.ad_soyad hasta, hk.ad_soyad hekim, r.islem, r.durum
            FROM randevular r LEFT JOIN hastalar h ON h.id=r.hasta_id
            LEFT JOIN hekimler hk ON hk.id=r.hekim_id
            WHERE r.tarih=? ORDER BY r.saat""", (bugun_str(),))
        for r in rows:
            tag = "ok" if r["durum"] == "Geldi" else ("kritik" if r["durum"] in ("Gelmedi", "İptal") else "odd")
            self.t_bugun.insert("", "end", values=(r["saat"], r["hasta"], r["hekim"], r["islem"], r["durum"]),
                                tags=(tag,))

        for i in self.t_borc.get_children():
            self.t_borc.delete(i)
        borclular = []
        for h in db.listele("SELECT id, ad_soyad, telefon FROM hastalar ORDER BY ad_soyad"):
            kalan, _, _ = hasta_borc(db, h["id"])
            if kalan > 0.5:
                borclular.append((h["ad_soyad"], h["telefon"], kalan))
        borclular.sort(key=lambda x: -x[2])
        for i, (ad, tel, kalan) in enumerate(borclular[:50]):
            self.t_borc.insert("", "end", values=(ad, tel, para_fmt(kalan)), tags=cift_tag(i))
