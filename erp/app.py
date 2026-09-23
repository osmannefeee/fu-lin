# -*- coding: utf-8 -*-
"""ErpPro ana uygulama: stok + cari + alış/satış + kasa."""
import os
import tkinter as tk
import traceback
from datetime import date
from tkinter import filedialog, messagebox, ttk

from . import SURUM
from .lisans import aktivasyon_formu, durum, kilit_goster
from .sabitler import (AD, BIRIMLER, CARI_TIP, FATURA_TIP, LISANS_TEL,
                       ODEME_YONTEM, RENK, SLOGAN)
from .veritabani import Veritabani, uygulama_dizini
from .yardim import (ayar, bugun, cari_bakiye, cari_sozluk, csv_yaz,
                     fatura_no_uret, stok_degeri, tl)


class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.report_callback_exception = self._hata
        self.title(f"Fu-Lin {AD} v{SURUM} — {SLOGAN}")
        self.geometry("1280x780")
        self.configure(bg="#0b1120")

        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except Exception:
            pass
        st.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        st.configure("TButton", font=("Segoe UI", 10), padding=6)
        st.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        st.configure("TFrame", background="#0b1120")
        st.configure("TLabel", background="#0b1120", foreground="#e8eef7")
        st.configure("TLabelframe", background="#0b1120", foreground="#e8eef7")
        st.configure("TLabelframe.Label", background="#0b1120", foreground=RENK)

        ust = tk.Frame(self, bg="#0d1426")
        ust.pack(fill="x")
        tk.Label(ust, text=f"  📦  {AD}", font=("Segoe UI", 15, "bold"),
                 bg="#0d1426", fg=RENK).pack(side="left", pady=10)
        tk.Label(ust, text=f"  {ayar(db, 'isletme')}  •  v{SURUM}", bg="#0d1426", fg="#93a1b8").pack(side="left")
        d = durum(db)
        if d["tip"] == "deneme":
            tk.Label(ust, text=f"  ⏳ {d['kalan']} gün  ", bg="#7c2d12", fg="#fed7aa",
                     font=("Segoe UI", 10, "bold")).pack(side="right", padx=4)
        ttk.Button(ust, text="⏻ Çıkış", command=self.cikis).pack(side="right", padx=8, pady=8)
        ttk.Button(ust, text="🔑 Lisans", command=self.lisans_penc).pack(side="right", padx=3, pady=8)
        ttk.Button(ust, text="💾 Yedek", command=self.yedek).pack(side="right", padx=3, pady=8)
        ttk.Button(ust, text="Yenile", command=self.yenile).pack(side="right", padx=3, pady=8)
        self.protocol("WM_DELETE_WINDOW", self.cikis)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)
        self.tp, self.ts, self.tc, self.tf, self.tkasa, self.tr = (
            ttk.Frame(self.nb, padding=10) for _ in range(6))
        for f, b in [(self.tp, "📊 Panel"), (self.ts, "📦 Stok"), (self.tc, "👥 Cari"),
                     (self.tf, "🧾 Alış / Satış"), (self.tkasa, "💰 Kasa"), (self.tr, "📈 Rapor")]:
            self.nb.add(f, text=f"  {b}  ")
        self.panel_kur()
        self.stok_kur()
        self.cari_kur()
        self.fatura_kur()
        self.kasa_kur()
        self.rapor_kur()
        self.yenile()

    # ---------- iskelet ----------
    def _hata(self, exc, val, tb):
        try:
            with open(os.path.join(uygulama_dizini(), "erp_hata.log"), "a", encoding="utf-8") as f:
                f.write(f"\n===== {date.today()} =====\n")
                traceback.print_exception(exc, val, tb, file=f)
        except Exception:
            pass
        try:
            messagebox.showerror("Hata", f"İşlem yapılamadı:\n{val}\n\nDetay: erp_hata.log")
        except Exception:
            pass

    def cikis(self):
        try:
            self.destroy()
        finally:
            os._exit(0)

    def agac(self, par, sut):
        t = ttk.Treeview(par, columns=[k for k, _, _ in sut], show="headings")
        for k, b, w in sut:
            t.heading(k, text=b)
            t.column(k, width=w)
        t.pack(fill="both", expand=True, pady=4)
        t.tag_configure("odd", background="#f8fafc")
        t.tag_configure("even", background="#ffffff")
        t.tag_configure("kritik", background="#fee2e2")
        t.tag_configure("ok", background="#dcfce7")
        return t

    def satir(self, t, i, vals, ozel=""):
        t.insert("", "end", values=vals, tags=(ozel or ("even" if i % 2 else "odd"),))

    def lisans_penc(self):
        w = tk.Toplevel(self)
        w.title("Lisans")
        w.geometry("360x360")
        d = durum(self.db)
        ttk.Label(w, text="✅ Tam lisans" if d["tip"] == "tam" else f"⏳ Deneme: {d['kalan']} gün",
                  font=("Segoe UI", 12, "bold")).pack(pady=10)
        if d["tip"] != "tam":
            ttk.Label(w, text=f"Satın alma: {LISANS_TEL}").pack()
            aktivasyon_formu(w, self.db)

    def yedek(self):
        klasor = filedialog.askdirectory(title="Yedek klasörü")
        if not klasor:
            return
        n = 0
        for tablo in ["urunler", "cariler", "faturalar", "fatura_kalem", "stok_hareket",
                      "hesaplar", "kasa_hareket", "ayarlar"]:
            rows = self.db.listele(f"SELECT * FROM {tablo}")
            with open(os.path.join(klasor, f"{tablo}.csv"), "w", newline="", encoding="utf-8-sig") as f:
                if rows:
                    import csv
                    w = csv.DictWriter(f, fieldnames=rows[0].keys())
                    w.writeheader()
                    for r in rows:
                        w.writerow(dict(r))
                    n += len(rows)
        messagebox.showinfo("Yedek", f"{n} kayıt yedeklendi.")

    # ---------- PANEL ----------
    def panel_kur(self):
        self.kart = tk.Frame(self.tp, bg="#0b1120")
        self.kart.pack(fill="x")
        self.deger = {}
        for i, (k, b) in enumerate([("stok", "📦 Stok Değeri"), ("kasa", "💰 Kasa Toplam"),
                                    ("alc", "💵 Alacak / Borç")]):
            f = tk.Frame(self.kart, bg=[RENK, "#0ea5e9", "#f59e0b"][i])
            f.grid(row=0, column=i, padx=6, sticky="ew")
            self.kart.columnconfigure(i, weight=1)
            tk.Label(f, text=b, bg=f["bg"], fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
            v = tk.Label(f, text="-", bg=f["bg"], fg="white", font=("Segoe UI", 18, "bold"))
            v.pack(pady=(0, 12))
            self.deger[k] = v
        alt = ttk.Frame(self.tp)
        alt.pack(fill="both", expand=True, pady=6)
        s1 = ttk.LabelFrame(alt, text="⚠️ Kritik Stok")
        s1.pack(side="left", fill="both", expand=True, padx=4)
        s2 = ttk.LabelFrame(alt, text="📋 Son Hareketler")
        s2.pack(side="left", fill="both", expand=True, padx=4)
        self.t_kritik = self.agac(s1, [("u", "Ürün", 220), ("m", "Miktar", 90)])
        self.t_son = self.agac(s2, [("t", "Tarih", 100), ("h", "Hareket", 260), ("u", "Tutar", 110)])

    # ---------- STOK ----------
    def stok_kur(self):
        u = ttk.Frame(self.ts)
        u.pack(fill="x", pady=4)
        ttk.Label(u, text="🔍").pack(side="left")
        self.sq = ttk.Entry(u, width=30)
        self.sq.pack(side="left", padx=4)
        self.sq.bind("<KeyRelease>", lambda e: self.yenile())
        ttk.Button(u, text="+ Ürün", command=self.urun_form).pack(side="right", padx=3)
        ttk.Button(u, text="Düzenle", command=self.urun_duzenle).pack(side="right", padx=3)
        ttk.Button(u, text="Giriş/Çıkış", command=self.stok_hareket).pack(side="right", padx=3)
        self.t_stok = self.agac(self.ts, [("id", "ID", 45), ("kod", "Kod", 90), ("ad", "Ürün", 200),
                                          ("m", "Miktar", 80), ("a", "Alış", 100), ("s", "Satış", 100)])

    def urun_form(self, kayit=None):
        w = tk.Toplevel(self)
        w.title("Ürün")
        w.geometry("360x460")
        alan = {}
        for et, k, v in [("Kod *", "kod", ""), ("Ad *", "ad", ""), ("Kategori", "kat", ""),
                         ("Birim", "bir", "Adet"), ("Alış fiyatı", "af", "0"),
                         ("Satış fiyatı", "sf", "0"), ("Kritik seviye", "kr", "5")]:
            ttk.Label(w, text=et).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(w)
            e.pack(padx=12, fill="x")
            e.insert(0, v)
            alan[k] = e
        if kayit:
            for k, kol in [("kod", "kod"), ("ad", "ad"), ("kat", "kategori"), ("bir", "birim"),
                           ("af", "alis_fiyat"), ("sf", "satis_fiyat"), ("kr", "kritik")]:
                alan[k].delete(0, "end")
                alan[k].insert(0, str(kayit[kol] or ""))
        if kayit is None:
            pass

        def k():
            if not alan["kod"].get().strip() or not alan["ad"].get().strip():
                messagebox.showwarning("Uyarı", "Kod ve ad zorunlu.", parent=w)
                return
            try:
                af, sf, kr = float(alan["af"].get() or 0), float(alan["sf"].get() or 0), float(alan["kr"].get() or 5)
            except ValueError:
                messagebox.showwarning("Uyarı", "Fiyatlar sayısal olmalı.", parent=w)
                return
            import sqlite3
            try:
                if kayit:
                    self.db.sorgu("""UPDATE urunler SET kod=?,ad=?,kategori=?,birim=?,
                        alis_fiyat=?,satis_fiyat=?,kritik=? WHERE id=?""",
                        (alan["kod"].get().strip(), alan["ad"].get().strip(), alan["kat"].get().strip(),
                         alan["bir"].get() or "Adet", af, sf, kr, kayit["id"]))
                else:
                    self.db.sorgu("""INSERT INTO urunler(kod,ad,kategori,birim,alis_fiyat,satis_fiyat,kritik)
                                     VALUES(?,?,?,?,?,?,?)""",
                                  (alan["kod"].get().strip(), alan["ad"].get().strip(), alan["kat"].get().strip(),
                                   alan["bir"].get() or "Adet", af, sf, kr))
            except sqlite3.IntegrityError:
                messagebox.showwarning("Uyarı", "Bu kod zaten var.", parent=w)
                return
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def secili_urun(self):
        s = self.t_stok.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM urunler WHERE id=?",
                               (self.t_stok.item(s[0])["values"][0],))[0]

    def urun_duzenle(self):
        k = self.secili_urun()
        if k:
            self.urun_form(k)

    def stok_hareket(self):
        u = self.secili_urun()
        if not u:
            return
        w = tk.Toplevel(self)
        w.title("Stok Hareket")
        w.geometry("300x220")
        ttk.Label(w, text=f"{u['ad']} (mevcut: {u['miktar']})").pack(pady=6)
        ttk.Label(w, text="Miktar (+ giriş / - çıkış):").pack()
        e = ttk.Entry(w)
        e.pack(padx=12, fill="x", pady=4)
        ttk.Label(w, text="Neden:").pack()
        en = ttk.Entry(w)
        en.pack(padx=12, fill="x")

        def k():
            try:
                d = float(e.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Sayısal girin.", parent=w)
                return
            self.db.sorgu("UPDATE urunler SET miktar=miktar+? WHERE id=?", (d, u["id"]))
            self.db.sorgu("INSERT INTO stok_hareket(tarih,urun_id,degisim,neden) VALUES(?,?,?,?)",
                          (bugun(), u["id"], d, en.get().strip() or "Manuel"))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=k).pack(pady=10)

    # ---------- CARİ ----------
    def cari_kur(self):
        u = ttk.Frame(self.tc)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Cari", command=self.cari_form).pack(side="right", padx=3)
        ttk.Button(u, text="Düzenle", command=self.cari_duzenle).pack(side="right", padx=3)
        ttk.Button(u, text="Sil", command=self.cari_sil).pack(side="right", padx=3)
        self.t_cari = self.agac(self.tc, [("id", "ID", 45), ("t", "Tip", 90), ("u", "Unvan", 220),
                                          ("t2", "Telefon", 130), ("b", "Bakiye", 120)])

    def cari_form(self, kayit=None):
        w = tk.Toplevel(self)
        w.title("Cari")
        w.geometry("360x400")
        ttk.Label(w, text="Tip").pack(anchor="w", padx=12, pady=(8, 0))
        ct = ttk.Combobox(w, values=CARI_TIP, state="readonly")
        ct.pack(padx=12, fill="x")
        ct.set("Müşteri")
        alan = {}
        for et, k in [("Unvan *", "unvan"), ("Yetkili", "yetkili"), ("Telefon", "tel"),
                      ("Adres", "adres"), ("Notlar", "not")]:
            ttk.Label(w, text=et).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(w)
            e.pack(padx=12, fill="x")
            alan[k] = e
        if kayit:
            ct.set(kayit["tip"])
            for k, e in alan.items():
                e.insert(0, {"unvan": kayit["unvan"], "yetkili": kayit["yetkili"], "tel": kayit["telefon"],
                             "adres": kayit["adres"], "not": kayit["notlar"]}[k] or "")

        def k():
            if not alan["unvan"].get().strip():
                messagebox.showwarning("Uyarı", "Unvan zorunlu.", parent=w)
                return
            v = [alan[x].get().strip() for x in ("unvan", "yetkili", "tel", "adres", "not")]
            if kayit:
                self.db.sorgu("UPDATE cariler SET tip=?,unvan=?,yetkili=?,telefon=?,adres=?,notlar=? WHERE id=?",
                              (ct.get(), *v, kayit["id"]))
            else:
                self.db.sorgu("INSERT INTO cariler(tip,unvan,yetkili,telefon,adres,notlar) VALUES(?,?,?,?,?,?)",
                              (ct.get(), *v))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def secili_cari(self):
        s = self.t_cari.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM cariler WHERE id=?",
                               (self.t_cari.item(s[0])["values"][0],))[0]

    def cari_duzenle(self):
        k = self.secili_cari()
        if k:
            self.cari_form(k)

    def cari_sil(self):
        k = self.secili_cari()
        if k and messagebox.askyesno("Onay", "Cari silinsin mi? (faturaları kalır)"):
            self.db.sorgu("DELETE FROM cariler WHERE id=?", (k["id"],))
            self.yenile()

    # ---------- FATURA ----------
    def fatura_kur(self):
        u = ttk.Frame(self.tf)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Satış Faturası", command=lambda: self.fatura_form("Satış")).pack(side="right", padx=3)
        ttk.Button(u, text="+ Alış Faturası", command=lambda: self.fatura_form("Alış")).pack(side="right", padx=3)
        ttk.Button(u, text="Sil (stok geri alınır)", command=self.fatura_sil).pack(side="right", padx=3)
        self.t_fat = self.agac(self.tf, [("id", "ID", 40), ("t", "Tip", 60), ("no", "No", 110),
                                         ("c", "Cari", 200), ("g", "Genel", 120), ("d", "Tarih", 100)])

    def fatura_form(self, tip):
        cariler = cari_sozluk(self.db, "Müşteri" if tip == "Satış" else "Tedarikçi")
        if not cariler:
            messagebox.showinfo("Bilgi", "Önce ilgili tipte cari ekleyin.")
            return
        urunler = {f"{r['kod']} - {r['ad']}": r for r in self.db.listele("SELECT * FROM urunler ORDER BY ad")}
        w = tk.Toplevel(self)
        w.title(f"{tip} Faturası")
        w.geometry("480x560")
        ttk.Label(w, text="Cari *").pack(anchor="w", padx=12, pady=(8, 0))
        cc = ttk.Combobox(w, values=list(cariler.keys()))
        cc.pack(padx=12, fill="x")
        fr = ttk.Frame(w)
        fr.pack(fill="x", padx=12, pady=6)
        ttk.Label(fr, text="KDV %:").pack(side="left")
        ek = ttk.Entry(fr, width=8)
        ek.pack(side="left", padx=4)
        ek.insert(0, "20")
        ttk.Button(fr, text="+ Kalem", command=lambda: kalem_ekle()).pack(side="right")
        lst = tk.Listbox(w, height=10)
        lst.pack(padx=12, fill="both", expand=True)
        kalemler = []

        def kalem_ekle():
            k = tk.Toplevel(w)
            k.title("Kalem")
            k.geometry("340x260")
            ttk.Label(k, text="Ürün").pack(anchor="w", padx=10, pady=(8, 0))
            cu = ttk.Combobox(k, values=list(urunler.keys()))
            cu.pack(padx=10, fill="x")
            ttk.Label(k, text="Adet").pack(anchor="w", padx=10, pady=(8, 0))
            ed = ttk.Entry(k)
            ed.pack(padx=10, fill="x")
            ed.insert(0, "1")
            ttk.Label(k, text="Birim fiyat (boş=liste)").pack(anchor="w", padx=10, pady=(8, 0))
            ef = ttk.Entry(k)
            ef.pack(padx=10, fill="x")

            def secim(e=None):
                if cu.get() in urunler:
                    r = urunler[cu.get()]
                    ef.delete(0, "end")
                    ef.insert(0, str(r["satis_fiyat"] if tip == "Satış" else r["alis_fiyat"]))
            cu.bind("<<ComboboxSelected>>", secim)

            def ekle():
                if cu.get() not in urunler:
                    messagebox.showwarning("Uyarı", "Ürün seçin.", parent=k)
                    return
                try:
                    ad = float(ed.get() or 1)
                    if ad <= 0:
                        raise ValueError
                    fi = float(ef.get() or 0)
                except ValueError:
                    messagebox.showwarning("Uyarı", "Sayısal girin.", parent=k)
                    return
                r = urunler[cu.get()]
                if tip == "Satış" and (r["miktar"] or 0) < ad:
                    if not messagebox.askyesno("Stok", f"Stok yetersiz ({r['miktar']}). Yine de ekle?", parent=k):
                        return
                kalemler.append((r["id"], r["ad"], ad, fi))
                lst.insert("end", f"{r['ad']} — {ad:g} x {tl(fi)}")
                k.destroy()

            ttk.Button(k, text="Ekle", command=ekle).pack(pady=10)

        def k():
            if cc.get() not in cariler:
                messagebox.showwarning("Uyarı", "Cari seçin.", parent=w)
                return
            if not kalemler:
                messagebox.showwarning("Uyarı", "En az bir kalem ekleyin.", parent=w)
                return
            try:
                oran = float(ek.get() or 20)
            except ValueError:
                oran = 20
            ara = sum(a * f for _, _, a, f in kalemler)
            kdv = round(ara * oran / 100, 2)
            no = fatura_no_uret(self.db, tip)
            cur = self.db.sorgu("""INSERT INTO faturalar(tip,no,cari_id,tarih,ara_toplam,kdv_oran,kdv,genel)
                                   VALUES(?,?,?,?,?,?,?,?)""",
                                (tip, no, cariler[cc.get()], bugun(), round(ara, 2), oran, kdv, round(ara + kdv, 2)))
            fid = cur.lastrowid
            yon = -1 if tip == "Satış" else 1
            for uid, ad, a, f in kalemler:
                self.db.sorgu("INSERT INTO fatura_kalem(fatura_id,urun_id,urun,adet,fiyat) VALUES(?,?,?,?,?)",
                              (fid, uid, ad, a, f))
                self.db.sorgu("UPDATE urunler SET miktar=miktar+? WHERE id=?", (yon * a, uid))
                self.db.sorgu("INSERT INTO stok_hareket(tarih,urun_id,degisim,neden) VALUES(?,?,?,?)",
                              (bugun(), uid, yon * a, f"{tip} {no}"))
            w.destroy()
            self.yenile()
            messagebox.showinfo("Fatura", f"{no} kesildi. Stok işlendi.")

        ttk.Button(w, text="Faturayı Kes", command=k).pack(pady=10)

    def fatura_sil(self):
        s = self.t_fat.selection()
        if not s:
            return
        fid = self.t_fat.item(s[0])["values"][0]
        f = self.db.listele("SELECT * FROM faturalar WHERE id=?", (fid,))[0]
        if not messagebox.askyesno("Onay", f"{f['no']} silinsin mi? Stok geri alınır."):
            return
        yon = 1 if f["tip"] == "Satış" else -1
        for k in self.db.listele("SELECT * FROM fatura_kalem WHERE fatura_id=?", (fid,)):
            self.db.sorgu("UPDATE urunler SET miktar=miktar+? WHERE id=?", (yon * k["adet"], k["urun_id"]))
        self.db.sorgu("DELETE FROM fatura_kalem WHERE fatura_id=?", (fid,))
        self.db.sorgu("DELETE FROM faturalar WHERE id=?", (fid,))
        self.yenile()

    # ---------- KASA ----------
    def kasa_kur(self):
        u = ttk.Frame(self.tkasa)
        u.pack(fill="x", pady=4)
        self.kasa_ozet = ttk.Label(u, text="", font=("Segoe UI", 11, "bold"))
        self.kasa_ozet.pack(side="left")
        ttk.Button(u, text="+ Tahsilat", command=lambda: self.kasa_form("Giriş")).pack(side="right", padx=3)
        ttk.Button(u, text="+ Ödeme", command=lambda: self.kasa_form("Çıkış")).pack(side="right", padx=3)
        ttk.Button(u, text="+ Hesap", command=self.hesap_form).pack(side="right", padx=3)
        self.t_kasa = self.agac(self.tkasa, [("t", "Tarih", 100), ("h", "Hesap", 130), ("y", "Yön", 70),
                                             ("c", "Cari", 180), ("u", "Tutar", 120), ("a", "Açıklama", 200)])

    def hesap_form(self):
        w = tk.Toplevel(self)
        w.title("Hesap")
        w.geometry("300x200")
        ttk.Label(w, text="Ad *").pack(anchor="w", padx=12, pady=(8, 0))
        ea = ttk.Entry(w)
        ea.pack(padx=12, fill="x")
        ttk.Label(w, text="Tür").pack(anchor="w", padx=12, pady=(8, 0))
        ct = ttk.Combobox(w, values=["Kasa", "Banka"], state="readonly")
        ct.pack(padx=12, fill="x")
        ct.set("Kasa")

        def k():
            if ea.get().strip():
                self.db.sorgu("INSERT OR IGNORE INTO hesaplar(ad,tur) VALUES(?,?)",
                              (ea.get().strip(), ct.get()))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=10)

    def kasa_form(self, yon):
        hesaplar = [r["ad"] for r in self.db.listele("SELECT * FROM hesaplar ORDER BY ad")]
        cariler = cari_sozluk(self.db)
        w = tk.Toplevel(self)
        w.title("Tahsilat" if yon == "Giriş" else "Ödeme")
        w.geometry("360x380")
        ttk.Label(w, text="Hesap").pack(anchor="w", padx=12, pady=(8, 0))
        ch = ttk.Combobox(w, values=hesaplar, state="readonly")
        ch.pack(padx=12, fill="x")
        if hesaplar:
            ch.set(hesaplar[0])
        ttk.Label(w, text="Cari (opsiyonel)").pack(anchor="w", padx=12, pady=(8, 0))
        cc = ttk.Combobox(w, values=[""] + list(cariler.keys()))
        cc.pack(padx=12, fill="x")
        ttk.Label(w, text="Tutar *").pack(anchor="w", padx=12, pady=(8, 0))
        eu = ttk.Entry(w)
        eu.pack(padx=12, fill="x")
        ttk.Label(w, text="Açıklama").pack(anchor="w", padx=12, pady=(8, 0))
        ea = ttk.Entry(w)
        ea.pack(padx=12, fill="x")

        def k():
            try:
                u = float(eu.get())
                if u <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli tutar girin.", parent=w)
                return
            hid = self.db.listele("SELECT id FROM hesaplar WHERE ad=?", (ch.get(),))[0]["id"]
            self.db.sorgu("""INSERT INTO kasa_hareket(tarih,hesap_id,yon,tutar,cari_id,aciklama)
                             VALUES(?,?,?,?,?,?)""",
                          (bugun(), hid, yon, u, cariler.get(cc.get()), ea.get().strip()))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    # ---------- RAPOR ----------
    def rapor_kur(self):
        bar = ttk.Frame(self.tr)
        bar.pack(fill="x", pady=4)
        ttk.Label(bar, text="📈 Rapor", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(bar, text="⬇ CSV: Stok", command=lambda: self.rapor_csv("stok")).pack(side="right", padx=3)
        ttk.Button(bar, text="⬇ CSV: Faturalar", command=lambda: self.rapor_csv("fat")).pack(side="right", padx=3)
        ttk.Button(bar, text="⬇ CSV: Cari", command=lambda: self.rapor_csv("cari")).pack(side="right", padx=3)
        self.rapor_txt = tk.Text(self.tr, height=25, font=("Consolas", 10), bg="#0d1426", fg="#a7f3d0")
        self.rapor_txt.pack(fill="both", expand=True)

    def rapor_csv(self, tur):
        klasor = filedialog.askdirectory(title="CSV klasörü")
        if not klasor:
            return
        db = self.db
        if tur == "stok":
            rows = db.listele("SELECT kod,ad,kategori,miktar,alis_fiyat,satis_fiyat FROM urunler ORDER BY ad")
            csv_yaz(klasor, "stok.csv", ["Kod", "Ad", "Kategori", "Miktar", "Alış", "Satış"],
                    [[r["kod"], r["ad"], r["kategori"], r["miktar"], r["alis_fiyat"], r["satis_fiyat"]] for r in rows])
        elif tur == "fat":
            rows = db.listele("""SELECT f.tip,f.no,c.unvan,f.tarih,f.genel FROM faturalar f
                LEFT JOIN cariler c ON c.id=f.cari_id ORDER BY f.id DESC""")
            csv_yaz(klasor, "faturalar.csv", ["Tip", "No", "Cari", "Tarih", "Genel"],
                    [[r["tip"], r["no"], r["unvan"], r["tarih"], r["genel"]] for r in rows])
        else:
            rows = db.listele("SELECT id,tip,unvan,telefon FROM cariler ORDER BY unvan")
            csv_yaz(klasor, "cariler.csv", ["ID", "Tip", "Unvan", "Telefon"],
                    [[r["id"], r["tip"], r["unvan"], r["telefon"]] for r in rows])
        messagebox.showinfo("CSV", f"Dışa aktarıldı:\n{klasor}")

    # ---------- YENİLE ----------
    def yenile(self):
        db = self.db
        ay = date.today().strftime("%Y-%m")
        self.deger["stok"].config(text=tl(stok_degeri(db)))
        kt = db.listele("""SELECT COALESCE(SUM(CASE WHEN yon='Giriş' THEN tutar ELSE -tutar END),0) s
                           FROM kasa_hareket""")[0]["s"] or 0
        self.deger["kasa"].config(text=tl(kt))
        alc = sum(cari_bakiye(db, r["id"]) for r in db.listele("SELECT id FROM cariler WHERE tip='Müşteri'"))
        borc = -sum(cari_bakiye(db, r["id"]) for r in db.listele("SELECT id FROM cariler WHERE tip='Tedarikçi'"))
        self.deger["alc"].config(text=f"{tl(alc)} / {tl(borc)}")

        for i in self.t_kritik.get_children():
            self.t_kritik.delete(i)
        for r in db.listele("SELECT * FROM urunler WHERE miktar<=kritik ORDER BY ad LIMIT 50"):
            self.t_kritik.insert("", "end", values=(r["ad"], r["miktar"]), tags=("kritik",))
        for i in self.t_son.get_children():
            self.t_son.delete(i)
        for r in db.listele("""SELECT k.tarih, h.ad hesap, k.yon, k.tutar FROM kasa_hareket k
            LEFT JOIN hesaplar h ON h.id=k.hesap_id ORDER BY k.id DESC LIMIT 20"""):
            self.t_son.insert("", "end", values=(r["tarih"], f"{r['hesap']} {r['yon']}",
                                                 tl(r["tutar"])), tags=("odd",))

        q = (self.sq.get() or "").strip()
        for i in self.t_stok.get_children():
            self.t_stok.delete(i)
        rows = db.listele("SELECT * FROM urunler WHERE kod LIKE ? OR ad LIKE ? ORDER BY ad",
                          (f"%{q}%", f"%{q}%")) if q else db.listele("SELECT * FROM urunler ORDER BY ad LIMIT 400")
        for j, r in enumerate(rows):
            self.satir(self.t_stok, j, (r["id"], r["kod"], r["ad"], r["miktar"],
                                        tl(r["alis_fiyat"]), tl(r["satis_fiyat"])),
                       "kritik" if (r["miktar"] or 0) <= (r["kritik"] or 0) else "")
        for i in self.t_cari.get_children():
            self.t_cari.delete(i)
        for j, r in enumerate(db.listele("SELECT * FROM cariler ORDER BY unvan")):
            b = cari_bakiye(db, r["id"])
            self.satir(self.t_cari, j, (r["id"], r["tip"], r["unvan"], r["telefon"], tl(b)),
                       "kritik" if (r["tip"] == "Müşteri" and b > 0.5) or
                       (r["tip"] == "Tedarikçi" and b < -0.5) else "")
        for i in self.t_fat.get_children():
            self.t_fat.delete(i)
        for j, r in enumerate(db.listele("""SELECT f.*, c.unvan FROM faturalar f
            LEFT JOIN cariler c ON c.id=f.cari_id ORDER BY f.id DESC LIMIT 300""")):
            self.satir(self.t_fat, j, (r["id"], r["tip"], r["no"], r["unvan"], tl(r["genel"]), r["tarih"]))
        top_k = 0
        for i in self.t_kasa.get_children():
            self.t_kasa.delete(i)
        for j, r in enumerate(db.listele("""SELECT k.*, h.ad hesap, c.unvan FROM kasa_hareket k
            LEFT JOIN hesaplar h ON h.id=k.hesap_id LEFT JOIN cariler c ON c.id=k.cari_id
            ORDER BY k.id DESC LIMIT 200""")):
            self.satir(self.t_kasa, j, (r["tarih"], r["hesap"], r["yon"], r["unvan"] or "-",
                                        tl(r["tutar"]), r["aciklama"] or ""))
        hesaplar = [(r["ad"], db.listele("""SELECT COALESCE(SUM(CASE WHEN yon='Giriş' THEN tutar ELSE -tutar END),0) s
            FROM kasa_hareket WHERE hesap_id=?""", (r["id"],))[0]["s"] or 0)
            for r in db.listele("SELECT * FROM hesaplar")]
        self.kasa_ozet.config(text="  •  ".join(f"{a}: {tl(b)}" for a, b in hesaplar))
        sat = db.listele("SELECT COALESCE(SUM(genel),0) s FROM faturalar WHERE tip='Satış' AND substr(tarih,1,7)=?",
                         (ay,))[0]["s"] or 0
        als = db.listele("SELECT COALESCE(SUM(genel),0) s FROM faturalar WHERE tip='Alış' AND substr(tarih,1,7)=?",
                         (ay,))[0]["s"] or 0
        txt = [f"===== {ay} ERP RAPORU =====", f"Satış: {tl(sat)}", f"Alış: {tl(als)}",
               f"Brüt fark: {tl(sat - als)}", f"Stok değeri: {tl(stok_degeri(db))}", "",
               "--- Hesaplar ---"]
        txt += [f"{a}: {tl(b)}" for a, b in hesaplar]
        txt.append("")
        txt.append("--- Kritik Stok ---")
        txt += [f"{r['ad']}: {r['miktar']} {r['birim']}" for r in
                db.listele("SELECT * FROM urunler WHERE miktar<=kritik ORDER BY ad")] or ["(yok)"]
        self.rapor_txt.delete("1.0", "end")
        self.rapor_txt.insert("1.0", "\n".join(txt))


def main():
    db = Veritabani()
    if durum(db)["kilitli"] and not kilit_goster(db):
        return
    App(db).mainloop()
