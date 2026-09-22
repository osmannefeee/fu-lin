# -*- coding: utf-8 -*-
"""TamirPro ana uygulama: kurulum sihirbazı + profile göre şekillenen ekranlar."""
import csv
import os
import tkinter as tk
import traceback
from datetime import date
from tkinter import filedialog, messagebox, ttk

from . import SURUM
from .lisans import aktivasyon_formu, durum, kilit_goster
from .sabitler import LISANS_TEL, ODEME_YONTEM, PROFILLER, WA_NO
from .veritabani import Veritabani, uygulama_dizini
from .yardim import (ayar, bugun, csv_yaz, emir_bakiye, fatura_html, fatura_kes,
                     musteri_sozluk, sms_metni, tl, yarin)


def profil_secici():
    """İlk açılışta iş kolu seçtirir. Kayıtlı varsa onu döner."""
    for k, p in PROFILLER.items():
        yol = os.path.join(uygulama_dizini(), p["db"])
        if os.path.exists(yol):
            import sqlite3
            try:
                b = sqlite3.connect(yol)
                r = b.execute("SELECT deger FROM ayarlar WHERE anahtar='profil'").fetchone()
                b.close()
                if r:
                    return k
            except Exception:
                pass
    sec = {}
    r = tk.Tk()
    r.title("TamirPro Kurulum")
    r.geometry("520x420")
    r.configure(bg="#0b1120")
    tk.Label(r, text="🔧 TamirPro", font=("Segoe UI", 24, "bold"), bg="#0b1120", fg="white").pack(pady=(20, 4))
    tk.Label(r, text="Ne tür tamir yapıyorsun? Seç, sistem ona göre kurulsun.",
             bg="#0b1120", fg="#93a1b8", font=("Segoe UI", 11)).pack(pady=(0, 16))
    for k, p in PROFILLER.items():
        b = tk.Button(r, text=f"{p['ad']}\n{p['slogan']}", font=("Segoe UI", 12, "bold"),
                      bg=p["renk"], fg="white", relief="flat", cursor="hand2", width=34, height=2,
                      command=lambda k=k: (sec.update(profil=k), r.destroy()))
        b.pack(pady=6)
    r.mainloop()
    return sec.get("profil")


class App(tk.Tk):
    def __init__(self, db, p):
        super().__init__()
        self.db = db
        self.p = p
        self.report_callback_exception = self._hata
        self.title(f"{p['ad']} v{SURUM} — {p['slogan']}")
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
        st.configure("TLabelframe.Label", background="#0b1120", foreground=p["renk"])

        ust = tk.Frame(self, bg="#0d1426")
        ust.pack(fill="x")
        tk.Label(ust, text=f"  🔧  {p['ad']}", font=("Segoe UI", 15, "bold"),
                 bg="#0d1426", fg=p["renk"]).pack(side="left", pady=10)
        tk.Label(ust, text=f"  {ayar(db, 'isletme')}  •  v{SURUM}", bg="#0d1426", fg="#93a1b8").pack(side="left")
        d = durum(db)
        self.lisans = d
        if d["tip"] == "deneme":
            tk.Label(ust, text=f"  ⏳ {d['kalan']} gün  ", bg="#7c2d12", fg="#fed7aa",
                     font=("Segoe UI", 10, "bold")).pack(side="right", padx=4)
        ttk.Button(ust, text="⏻ Çıkış", command=self.cikis).pack(side="right", padx=8, pady=8)
        ttk.Button(ust, text="🔑 Lisans", command=self.lisans_penc).pack(side="right", padx=3, pady=8)
        ttk.Button(ust, text="⚙️ İşletme", command=self.isletme_ayar).pack(side="right", padx=3, pady=8)
        ttk.Button(ust, text="💾 Yedek", command=self.yedek).pack(side="right", padx=3, pady=8)
        ttk.Button(ust, text="Yenile", command=self.yenile).pack(side="right", padx=3, pady=8)
        self.protocol("WM_DELETE_WINDOW", self.cikis)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)
        self.tp, self.te, self.tm, self.ts, self.t_kasa, self.tr = (ttk.Frame(self.nb, padding=10) for _ in range(6))
        for f, b in [(self.tp, "📊 Panel"), (self.te, "🧾 İş Emirleri"), (self.tm, "👥 Müşteriler"),
                     (self.ts, "🔩 Parça & Stok"), (self.t_kasa, "💰 Kasa"), (self.tr, "✉️ SMS & Rapor")]:
            self.nb.add(f, text=f"  {b}  ")
        self.panel_kur()
        self.emir_kur()
        self.mus_kur()
        self.stok_kur()
        self.kasa_kur()
        self.sms_kur()
        self.yenile()

    # ---------- iskelet ----------
    def _hata(self, exc, val, tb):
        import traceback as t2
        try:
            with open(os.path.join(uygulama_dizini(), "tamir_hata.log"), "a", encoding="utf-8") as f:
                f.write(f"\n===== {date.today()} =====\n")
                t2.print_exception(exc, val, tb, file=f)
        except Exception:
            pass
        try:
            messagebox.showerror("Hata", f"İşlem yapılamadı:\n{val}\n\nDetay: tamir_hata.log")
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

    def isletme_ayar(self):
        w = tk.Toplevel(self)
        w.title("İşletme")
        w.geometry("340x200")
        ttk.Label(w, text="İşletme adı (fiş/SMS'te görünür):").pack(anchor="w", padx=12, pady=(10, 0))
        e = ttk.Entry(w)
        e.pack(padx=12, fill="x")
        e.insert(0, ayar(self.db, "isletme"))

        def k():
            ayar(self.db, "isletme", e.get().strip() or "Servisim")
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def yedek(self):
        klasor = filedialog.askdirectory(title="Yedek klasörü")
        if not klasor:
            return
        n = 0
        for tablo in ["musteriler", "is_emirleri", "emir_parca", "parcalar", "odemeler",
                      "faturalar", "sms_log", "ayarlar"]:
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
        for i, (k, b) in enumerate([("bek", "🔧 Bekleyen İş"), ("haz", "✅ Teslim Hazır"), ("ay", "💰 Ay Tahsilat")]):
            f = tk.Frame(self.kart, bg=[self.p["renk"], "#10b981", "#0ea5e9"][i])
            f.grid(row=0, column=i, padx=6, sticky="ew")
            self.kart.columnconfigure(i, weight=1)
            tk.Label(f, text=b, bg=f["bg"], fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
            v = tk.Label(f, text="0", bg=f["bg"], fg="white", font=("Segoe UI", 22, "bold"))
            v.pack(pady=(0, 12))
            self.deger[k] = v
        self.t_panel = self.agac(self.tp, [("no", "No", 60), ("m", "Müşteri", 200), ("c", "Cihaz", 220),
                                           ("d", "Durum", 130), ("b", "Kalan", 110)])

    # ---------- İŞ EMİRLERİ ----------
    def emir_kur(self):
        u = ttk.Frame(self.te)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Yeni İş Emri", command=self.emir_form).pack(side="right", padx=3)
        ttk.Button(u, text="Durum Seç", command=self.emir_durum_sec).pack(side="right", padx=3)
        ttk.Button(u, text="🧾 Fatura", command=self.fatura_penc).pack(side="right", padx=3)
        ttk.Button(u, text="🔩 Parça Ekle", command=self.parca_ekle).pack(side="right", padx=3)
        ttk.Button(u, text="💵 Tahsilat", command=self.emir_tahsilat).pack(side="right", padx=3)
        self.t_emir = self.agac(self.te, [("id", "No", 55), ("m", "Müşteri", 170), ("c", "Cihaz", 200),
                                          ("a", "Arıza", 170), ("t", "Tutar", 100), ("d", "Durum", 120)])

    def secili_emir(self):
        s = self.t_emir.selection()
        if not s:
            return None
        eid = self.t_emir.item(s[0])["values"][0]
        return self.db.listele("SELECT * FROM is_emirleri WHERE id=?", (eid,))[0]

    def emir_form(self):
        mus = musteri_sozluk(self.db)
        if not mus:
            messagebox.showinfo("Bilgi", "Önce müşteri ekleyin.")
            return
        w = tk.Toplevel(self)
        w.title("Yeni İş Emri")
        w.geometry("440x620")
        ttk.Label(w, text="Müşteri *").pack(anchor="w", padx=12, pady=(8, 0))
        cm = ttk.Combobox(w, values=list(mus.keys()))
        cm.pack(padx=12, fill="x")
        ttk.Label(w, text="Cihaz Türü").pack(anchor="w", padx=12, pady=(8, 0))
        ct = ttk.Combobox(w, values=self.p["cihaz_turleri"])
        ct.pack(padx=12, fill="x")
        ct.set(self.p["cihaz_turleri"][0])
        alan = {}
        for etiket, anahtar in self.p["alanlar"]:
            ttk.Label(w, text=etiket).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(w)
            e.pack(padx=12, fill="x")
            alan[anahtar] = e
        ttk.Label(w, text=self.p["birim_ad"]).pack(anchor="w", padx=12, pady=(8, 0))
        cb = ttk.Combobox(w, values=self.p["birimler"])
        cb.pack(padx=12, fill="x")
        cb.set(self.p["birimler"][0])
        ttk.Label(w, text="Arıza").pack(anchor="w", padx=12, pady=(8, 0))
        ca = ttk.Combobox(w, values=self.p["arizalar"])
        ca.pack(padx=12, fill="x")
        ttk.Label(w, text="Yapılacak işlem + işçilik").pack(anchor="w", padx=12, pady=(8, 0))
        fr = ttk.Frame(w)
        fr.pack(fill="x", padx=12)
        ci = ttk.Combobox(fr, values=list(self.p["islemler"].keys()), width=26)
        ci.pack(side="left")
        ci.set(list(self.p["islemler"].keys())[0])
        eu = ttk.Entry(fr, width=14)
        eu.pack(side="left", padx=6)
        eu.insert(0, str(list(self.p["islemler"].values())[0]))

        def secimdegisti(e=None):
            eu.delete(0, "end")
            eu.insert(0, str(self.p["islemler"].get(ci.get(), 0)))
        ci.bind("<<ComboboxSelected>>", secimdegisti)

        def k():
            if cm.get() not in mus:
                messagebox.showwarning("Uyarı", "Müşteri seçin.", parent=w)
                return
            try:
                iscilik = float(eu.get() or 0)
            except ValueError:
                messagebox.showwarning("Uyarı", "İşçilik sayısal olmalı.", parent=w)
                return
            v = {a: alan[a].get().strip() for a in alan}
            self.db.sorgu("""INSERT INTO is_emirleri
                (musteri_id, cihaz_tur, marka, model, seri, garanti, birim, ariza, yapilan,
                 iscilik, parca_tutar, toplam, durum, gelis)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (mus[cm.get()], ct.get(), v.get("marka"), v.get("model"), v.get("seri"),
                 v.get("garanti"), cb.get(), ca.get(), ci.get(), iscilik, 0, iscilik,
                 self.p["durumlar"][0], bugun()))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def emir_durum_sec(self):
        """Manuel durum seçimi: ileri de geri de alınabilir."""
        e = self.secili_emir()
        if not e:
            messagebox.showinfo("Bilgi", "Önce iş emri seçin.")
            return
        w = tk.Toplevel(self)
        w.title(f"Durum (Emir #{e['id']})")
        w.geometry("320x200")
        ttk.Label(w, text=f"Mevcut: {e['durum']}").pack(pady=8)
        cb = ttk.Combobox(w, values=self.p["durumlar"], state="readonly")
        cb.pack(padx=12, fill="x")
        cb.set(e["durum"])

        def uygula():
            self.db.sorgu("UPDATE is_emirleri SET durum=?, teslim=? WHERE id=?",
                          (cb.get(), bugun() if cb.get() == "Teslim Edildi" else e["teslim"], e["id"]))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=uygula).pack(pady=12)

    def parca_ekle(self):
        e = self.secili_emir()
        if not e:
            messagebox.showinfo("Bilgi", "Önce iş emri seçin.")
            return
        stok = {r["urun"]: (r["miktar"], r["fiyat"], r["id"]) for r in self.db.listele("SELECT * FROM parcalar ORDER BY urun")}
        w = tk.Toplevel(self)
        w.title(f"Parça Ekle (Emir #{e['id']})")
        w.geometry("360x300")
        ttk.Label(w, text="Parça (stoktan düşer)").pack(anchor="w", padx=12, pady=(8, 0))
        cp = ttk.Combobox(w, values=list(stok.keys()))
        cp.pack(padx=12, fill="x")
        ttk.Label(w, text="Adet").pack(anchor="w", padx=12, pady=(8, 0))
        ea = ttk.Entry(w)
        ea.pack(padx=12, fill="x")
        ea.insert(0, "1")

        def k():
            if cp.get() not in stok:
                messagebox.showwarning("Uyarı", "Stoktan parça seçin.", parent=w)
                return
            try:
                adet = float(ea.get() or 1)
                if adet <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", "Adet sayısal olmalı.", parent=w)
                return
            miktar, fiyat, sid = stok[cp.get()]
            if (miktar or 0) < adet:
                messagebox.showwarning("Uyarı", f"Stok yetersiz ({miktar}).", parent=w)
                return
            self.db.sorgu("INSERT INTO emir_parca(emir_id,urun,adet,fiyat) VALUES(?,?,?,?)",
                          (e["id"], cp.get(), adet, fiyat))
            self.db.sorgu("UPDATE parcalar SET miktar=miktar-? WHERE id=?", (adet, sid))
            tutar = adet * (fiyat or 0)
            self.db.sorgu("UPDATE is_emirleri SET parca_tutar=parca_tutar+?, toplam=toplam+? WHERE id=?",
                          (tutar, tutar, e["id"]))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Ekle", command=k).pack(pady=12)

    def fatura_penc(self):
        e = self.secili_emir()
        if not e:
            messagebox.showinfo("Bilgi", "Önce iş emri seçin.")
            return
        w = tk.Toplevel(self)
        w.title(f"Fatura (Emir #{e['id']})")
        w.geometry("380x220")
        ttk.Label(w, text="KDV oranı (%)").pack(anchor="w", padx=12, pady=(10, 0))
        ek = ttk.Entry(w)
        ek.pack(padx=12, fill="x")
        ek.insert(0, "20")
        ttk.Label(w, text="Not: gerçek e-Fatura entegrasyonu yakında.\nBu belge yazdırılabilir servis fişidir.",
                  font=("Segoe UI", 9)).pack(padx=12, pady=6)

        def kes():
            try:
                oran = float(ek.get() or 20)
            except ValueError:
                messagebox.showwarning("Uyarı", "KDV sayısal olmalı.", parent=w)
                return
            fat = fatura_kes(self.db, e["id"], oran)
            w.destroy()
            self.fatura_goster(e["id"], fat)

        ttk.Button(w, text="🧾 Faturayı Kes / Aç", command=kes).pack(pady=8, fill="x", padx=12)

    def fatura_goster(self, emir_id, fat):
        import tempfile
        import webbrowser
        e = self.db.listele("SELECT * FROM is_emirleri WHERE id=?", (emir_id,))[0]
        mus = self.db.listele("SELECT * FROM musteriler WHERE id=?", (e["musteri_id"],))[0]
        par = self.db.listele("SELECT * FROM emir_parca WHERE emir_id=?", (emir_id,))
        html = fatura_html(ayar(self.db, "isletme"), mus, e, par, fat)
        yol = os.path.join(tempfile.gettempdir(), f"fatura_{fat['no'].replace('-', '_')}.html")
        with open(yol, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open("file://" + yol.replace("\\", "/"))

        def wa_bildir():
            import urllib.parse
            m = urllib.parse.quote(f"Merhaba, {fat['no']} nolu servis faturanız hazır. Toplam: {tl(fat['genel'])}")
            webbrowser.open(f"https://wa.me/{WA_NO}?text={m}")

        w = tk.Toplevel(self)
        w.title(f"Fatura {fat['no']}")
        w.geometry("320x180")
        ttk.Label(w, text=f"Fatura {fat['no']} tarayıcıda açıldı.", font=("Segoe UI", 11, "bold")).pack(pady=12)
        ttk.Label(w, text=f"Toplam: {tl(fat['genel'])}").pack()
        ttk.Button(w, text="📩 Müşteriye WhatsApp ile Bildir", command=wa_bildir).pack(pady=12, fill="x", padx=12)

    def emir_tahsilat(self):
        e = self.secili_emir()
        if not e:
            return
        kalan, _, _ = emir_bakiye(self.db, e["id"])
        w = tk.Toplevel(self)
        w.title(f"Tahsilat (Emir #{e['id']})")
        w.geometry("320x280")
        ttk.Label(w, text=f"Kalan: {tl(kalan)}").pack(pady=8)
        ttk.Label(w, text="Tutar *").pack(anchor="w", padx=12)
        eu = ttk.Entry(w)
        eu.pack(padx=12, fill="x")
        eu.insert(0, str(int(kalan)) if kalan > 0 else "")
        ttk.Label(w, text="Yöntem").pack(anchor="w", padx=12, pady=(8, 0))
        cy = ttk.Combobox(w, values=["Nakit", "Kredi Kartı", "Havale/EFT", "Diğer"])
        cy.pack(padx=12, fill="x")
        cy.set("Nakit")

        def k():
            try:
                u = float(eu.get())
                if u <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli tutar girin.", parent=w)
                return
            self.db.sorgu("INSERT INTO odemeler(emir_id,musteri_id,tarih,tutar,yontem) VALUES(?,?,?,?,?)",
                          (e["id"], e["musteri_id"], bugun(), u, cy.get()))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    # ---------- MÜŞTERİLER ----------
    def mus_kur(self):
        u = ttk.Frame(self.tm)
        u.pack(fill="x", pady=4)
        ttk.Label(u, text="🔍").pack(side="left")
        self.mq = ttk.Entry(u, width=36)
        self.mq.pack(side="left", padx=4)
        self.mq.bind("<KeyRelease>", lambda e: self.yenile())
        ttk.Button(u, text="+ Müşteri", command=self.mus_form).pack(side="right")
        ttk.Button(u, text="Düzenle", command=self.mus_duzenle).pack(side="right", padx=4)
        self.t_mus = self.agac(self.tm, [("id", "ID", 50), ("ad", "Ad", 220), ("tel", "Tel", 140),
                                         ("is", "İş Sayısı", 90), ("borc", "Borç", 110)])
        self.t_mus.bind("<Double-1>", lambda e: self.mus_duzenle())

    def mus_form(self, kayit=None):
        w = tk.Toplevel(self)
        w.title("Müşteri")
        w.geometry("360x320")
        alan = {}
        for et, k in [("Ad Soyad *", "ad"), ("Telefon", "tel"), ("Adres", "adr"), ("Notlar", "not")]:
            ttk.Label(w, text=et).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(w)
            e.pack(padx=12, fill="x")
            if kayit:
                e.insert(0, {"ad": kayit["ad_soyad"], "tel": kayit["telefon"] or "",
                             "adr": kayit["adres"] or "", "not": kayit["notlar"] or ""}[k])
            alan[k] = e

        def k():
            if not alan["ad"].get().strip():
                messagebox.showwarning("Uyarı", "Ad boş olamaz.", parent=w)
                return
            try:
                if kayit:
                    self.db.sorgu("UPDATE musteriler SET ad_soyad=?,telefon=?,adres=?,notlar=? WHERE id=?",
                                  (alan["ad"].get().strip(), alan["tel"].get().strip(),
                                   alan["adr"].get().strip(), alan["not"].get().strip(), kayit["id"]))
                else:
                    self.db.sorgu("INSERT INTO musteriler(ad_soyad,telefon,adres,notlar) VALUES(?,?,?,?)",
                                  (alan["ad"].get().strip(), alan["tel"].get().strip(),
                                   alan["adr"].get().strip(), alan["not"].get().strip()))
            except Exception as ex:
                messagebox.showerror("Hata", f"Kayıt yazılamadı:\n{ex}", parent=w)
                return
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def secili_mus(self):
        s = self.t_mus.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM musteriler WHERE id=?", (self.t_mus.item(s[0])["values"][0],))[0]

    def mus_duzenle(self):
        k = self.secili_mus()
        if k:
            self.mus_form(k)

    # ---------- PARÇA & STOK ----------
    def stok_kur(self):
        u = ttk.Frame(self.ts)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Parça", command=self.stok_form).pack(side="right", padx=3)
        ttk.Button(u, text="+/-", command=self.stok_hareket).pack(side="right", padx=3)
        self.t_stok = self.agac(self.ts, [("id", "ID", 40), ("u", "Parça", 220), ("m", "Miktar", 80),
                                          ("f", "Fiyat", 110), ("k", "Kritik", 80)])

    def stok_form(self):
        w = tk.Toplevel(self)
        w.title("Parça")
        w.geometry("320x280")
        ttk.Label(w, text="Parça adı *").pack(anchor="w", padx=12, pady=(8, 0))
        eu = ttk.Entry(w)
        eu.pack(padx=12, fill="x")
        ttk.Label(w, text="Fiyat").pack(anchor="w", padx=12, pady=(8, 0))
        ef = ttk.Entry(w)
        ef.pack(padx=12, fill="x")
        ef.insert(0, "0")

        def k():
            if not eu.get().strip():
                return
            try:
                f = float(ef.get() or 0)
            except ValueError:
                f = 0
            self.db.sorgu("INSERT OR IGNORE INTO parcalar(urun,fiyat) VALUES(?,?)", (eu.get().strip(), f))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=10)

    def stok_hareket(self):
        s = self.t_stok.selection()
        if not s:
            return
        sid = self.t_stok.item(s[0])["values"][0]
        w = tk.Toplevel(self)
        w.title("Stok")
        w.geometry("260x160")
        ttk.Label(w, text="Miktar (+ giriş / - çıkış):").pack(pady=8)
        e = ttk.Entry(w)
        e.pack(padx=12, fill="x")

        def k():
            try:
                self.db.sorgu("UPDATE parcalar SET miktar=miktar+? WHERE id=?", (float(e.get()), sid))
            except ValueError:
                messagebox.showwarning("Uyarı", "Sayısal girin.", parent=w)
                return
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=k).pack(pady=8)

    # ---------- KASA ----------
    def kasa_kur(self):
        self.kasa_ozet = ttk.Label(self.t_kasa, text="", font=("Segoe UI", 12, "bold"))
        self.kasa_ozet.pack(anchor="w", pady=4)
        self.t_kasa = self.agac(self.t_kasa, [("t", "Tarih", 100), ("e", "Emir", 70), ("m", "Müşteri", 200),
                                          ("u", "Tutar", 120), ("y", "Yöntem", 120)])

    # ---------- SMS & RAPOR ----------
    def sms_kur(self):
        u = ttk.Frame(self.tr)
        u.pack(fill="x", pady=4)
        ttk.Label(u, text="Durumu değişen işleri SMS ile bildir").pack(side="left")
        ttk.Button(u, text="✉️ Hazır Olanlara SMS", command=self.sms_hazir).pack(side="right", padx=3)
        ttk.Button(u, text="⚙️ Şablon", command=self.sms_sablon).pack(side="right", padx=3)
        self.sms_txt = tk.Text(self.tr, height=8, font=("Segoe UI", 10))
        self.sms_txt.pack(fill="x", pady=4)
        ttk.Label(self.tr, text="📈 Rapor", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        rb = ttk.Frame(self.tr)
        rb.pack(fill="x", pady=4)
        ttk.Button(rb, text="⬇ CSV: İş Emirleri", command=lambda: self.rapor_csv("emir")).pack(side="left", padx=3)
        ttk.Button(rb, text="⬇ CSV: Kasa", command=lambda: self.rapor_csv("kasa")).pack(side="left", padx=3)
        ttk.Button(rb, text="⬇ CSV: Müşteriler", command=lambda: self.rapor_csv("mus")).pack(side="left", padx=3)
        ttk.Button(rb, text="⬇ CSV: Parçalar", command=lambda: self.rapor_csv("parca")).pack(side="left", padx=3)
        self.rapor_txt = tk.Text(self.tr, height=10, font=("Consolas", 10), bg="#0d1426", fg="#a7f3d0")
        self.rapor_txt.pack(fill="both", expand=True)

    def sms_hazir(self):
        rows = self.db.listele("""SELECT e.id, m.ad_soyad ad, m.telefon tel, e.durum FROM is_emirleri e
            LEFT JOIN musteriler m ON m.id=e.musteri_id WHERE e.durum='Hazır' ORDER BY e.id DESC LIMIT 50""")
        self.sms_txt.delete("1.0", "end")
        if not rows:
            self.sms_txt.insert("1.0", "'Hazır' durumunda iş emri yok.")
            return
        for r in rows:
            m = sms_metni(self.db, r["ad"], f"#{r['id']}", r["durum"])
            self.db.sorgu("INSERT INTO sms_log(tarih,telefon,mesaj,durum) VALUES(?,?,?,?)",
                          (bugun(), r["tel"], m, "Hazırlandı"))
            self.sms_txt.insert("end", f"📱 {r['tel']} → {m}\n\n")
        self.clipboard_clear()
        self.clipboard_append(self.sms_txt.get("1.0", "end").strip())
        messagebox.showinfo("SMS", f"{len(rows)} mesaj hazır, kopyalandı.")

    def sms_sablon(self):
        w = tk.Toplevel(self)
        w.title("SMS Şablonu")
        w.geometry("420x200")
        ttk.Label(w, text="Değişkenler: {ad} {no} {durum} {isletme}").pack(anchor="w", padx=12, pady=(8, 0))
        e = ttk.Entry(w)
        e.pack(padx=12, fill="x")
        e.insert(0, ayar(self.db, "sms_sablon"))

        def k():
            ayar(self.db, "sms_sablon", e.get())
            w.destroy()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=10)

    # ---------- YENİLE ----------
    def yenile(self):
        db = self.db
        ay = date.today().strftime("%Y-%m")
        bek = db.listele("SELECT COUNT(*) s FROM is_emirleri WHERE durum NOT IN ('Teslim Edildi','İptal')")[0]["s"]
        haz = db.listele("SELECT COUNT(*) s FROM is_emirleri WHERE durum='Hazır'")[0]["s"]
        ciro = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler WHERE substr(tarih,1,7)=?", (ay,))[0]["s"] or 0
        self.deger["bek"].config(text=str(bek))
        self.deger["haz"].config(text=str(haz))
        self.deger["ay"].config(text=tl(ciro))

        for t in (self.t_panel, self.t_emir, self.t_mus, self.t_stok, self.t_kasa):
            for i in t.get_children():
                t.delete(i)
        i = 0
        for r in db.listele("""SELECT e.id, m.ad_soyad ad, e.marka, e.model, e.durum, e.toplam
            FROM is_emirleri e LEFT JOIN musteriler m ON m.id=e.musteri_id
            WHERE e.durum NOT IN ('Teslim Edildi','İptal') ORDER BY e.id DESC LIMIT 100"""):
            kalan, _, _ = emir_bakiye(db, r["id"])
            tag = "ok" if r["durum"] == "Hazır" else ("even" if i % 2 else "odd")
            self.t_panel.insert("", "end", values=(r["id"], r["ad"], f"{r['marka'] or ''} {r['model'] or ''}",
                                                   r["durum"], tl(kalan)), tags=(tag,))
            i += 1
        i = 0
        for r in db.listele("""SELECT e.*, m.ad_soyad ad FROM is_emirleri e
            LEFT JOIN musteriler m ON m.id=e.musteri_id ORDER BY e.id DESC LIMIT 300"""):
            tag = "ok" if r["durum"] in ("Hazır", "Teslim Edildi") else \
                ("kritik" if r["durum"] == "İptal" else ("even" if i % 2 else "odd"))
            self.t_emir.insert("", "end", values=(r["id"], r["ad"], f"{r['marka'] or ''} {r['model'] or ''}",
                                                  r["ariza"], tl(r["toplam"]), r["durum"]), tags=(tag,))
            i += 1
        q = (self.mq.get() or "").strip()
        rows = db.listele("SELECT * FROM musteriler WHERE ad_soyad LIKE ? OR telefon LIKE ? ORDER BY ad_soyad",
                          (f"%{q}%", f"%{q}%")) if q else db.listele("SELECT * FROM musteriler ORDER BY ad_soyad LIMIT 400")
        for j, m in enumerate(rows):
            nis = db.listele("SELECT COUNT(*) s FROM is_emirleri WHERE musteri_id=?", (m["id"],))[0]["s"]
            borc = db.listele("""SELECT COALESCE(SUM(e.toplam),0)-COALESCE(
                (SELECT SUM(tutar) FROM odemeler o WHERE o.musteri_id=e.musteri_id),0) b
                FROM is_emirleri e WHERE e.musteri_id=?""", (m["id"],))[0]["b"] or 0
            self.satir(self.t_mus, j, (m["id"], m["ad_soyad"], m["telefon"], nis, tl(borc)),
                       "kritik" if borc > 0.5 else "")
        for j, r in enumerate(db.listele("SELECT * FROM parcalar ORDER BY urun")):
            self.satir(self.t_stok, j, (r["id"], "⚠️ " + r["urun"] if (r["miktar"] or 0) <= (r["kritik"] or 0) else r["urun"],
                                        r["miktar"], tl(r["fiyat"]), r["kritik"]))
        tah = 0
        for j, r in enumerate(db.listele("""SELECT o.tarih, o.tutar, o.yontem, e.id eid, m.ad_soyad ad
            FROM odemeler o LEFT JOIN is_emirleri e ON e.id=o.emir_id
            LEFT JOIN musteriler m ON m.id=o.musteri_id ORDER BY o.id DESC LIMIT 200""")):
            self.satir(self.t_kasa, j, (r["tarih"], f"#{r['eid']}" if r["eid"] else "-", r["ad"], tl(r["tutar"]), r["yontem"]))
            tah += r["tutar"] or 0
        self.kasa_ozet.config(text=f"Toplam tahsilat: {tl(tah)}  |  Bu ay: {tl(ciro)}")
        nis = db.listele("SELECT COUNT(*) s FROM is_emirleri WHERE substr(gelis,1,7)=?", (ay,))[0]["s"]
        kesilen = db.listele("SELECT COALESCE(SUM(toplam),0) s FROM is_emirleri WHERE substr(gelis,1,7)=?",
                             (ay,))[0]["s"] or 0
        tah_ay = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler WHERE substr(tarih,1,7)=?",
                            (ay,))[0]["s"] or 0
        sat = [f"===== {ay} SERVİS RAPORU =====", f"Alınan iş: {nis}",
               f"Kesilen tutar: {tl(kesilen)}", f"Tahsilat: {tl(tah_ay)}",
               f"Alacak: {tl(kesilen - tah_ay)}", "", "--- Durum Dağılımı ---"]
        for r in db.listele("SELECT durum, COUNT(*) n FROM is_emirleri GROUP BY durum"):
            sat.append(f"{r['durum']}: {r['n']}")
        sat.append("")
        sat.append("--- Cihaz Türü Bazında ---")
        for r in db.listele("""SELECT cihaz_tur, COUNT(*) n, COALESCE(SUM(toplam),0) t
            FROM is_emirleri WHERE substr(gelis,1,7)=? GROUP BY cihaz_tur ORDER BY t DESC""", (ay,)):
            sat.append(f"{r['cihaz_tur'] or '?'}: {r['n']} iş, {tl(r['t'])}")
        sat.append("")
        sat.append("--- En Çok Kullanılan Parçalar ---")
        for r in db.listele("""SELECT urun, SUM(adet) a, SUM(adet*fiyat) t FROM emir_parca
            GROUP BY urun ORDER BY a DESC LIMIT 10"""):
            sat.append(f"{r['urun']}: {r['a']:g} adet, {tl(r['t'])}")
        sat.append("")
        ort = db.listele("""SELECT AVG(julianday(teslim)-julianday(gelis)) o FROM is_emirleri
            WHERE durum='Teslim Edildi' AND gelis<>'' AND teslim<>''""")[0]["o"]
        sat.append(f"Ortalama tamir süresi: {(ort or 0):.1f} gün")
        self.rapor_txt.delete("1.0", "end")
        self.rapor_txt.insert("1.0", "\n".join(sat))

    def rapor_csv(self, tur):
        klasor = filedialog.askdirectory(title="CSV klasörü seçin")
        if not klasor:
            return
        db = self.db
        if tur == "emir":
            rows = db.listele("""SELECT e.id, m.ad_soyad, m.telefon, e.cihaz_tur, e.marka, e.model,
                e.ariza, e.yapilan, e.toplam, e.durum, e.gelis, e.teslim FROM is_emirleri e
                LEFT JOIN musteriler m ON m.id=e.musteri_id ORDER BY e.id DESC""")
            csv_yaz(klasor, "is_emirleri.csv",
                    ["No", "Müşteri", "Telefon", "Cihaz", "Marka", "Model", "Arıza",
                     "Yapılan", "Tutar", "Durum", "Geliş", "Teslim"],
                    [[r["id"], r["ad_soyad"], r["telefon"], r["cihaz_tur"], r["marka"], r["model"],
                      r["ariza"], r["yapilan"], r["toplam"], r["durum"], r["gelis"], r["teslim"]] for r in rows])
        elif tur == "kasa":
            rows = db.listele("""SELECT o.tarih, e.id, m.ad_soyad, o.tutar, o.yontem FROM odemeler o
                LEFT JOIN is_emirleri e ON e.id=o.emir_id
                LEFT JOIN musteriler m ON m.id=o.musteri_id ORDER BY o.id DESC""")
            csv_yaz(klasor, "kasa.csv", ["Tarih", "Emir", "Müşteri", "Tutar", "Yöntem"],
                    [[r["tarih"], r["id"], r["ad_soyad"], r["tutar"], r["yontem"]] for r in rows])
        elif tur == "mus":
            rows = db.listele("SELECT id, ad_soyad, telefon, adres FROM musteriler ORDER BY ad_soyad")
            csv_yaz(klasor, "musteriler.csv", ["ID", "Ad", "Telefon", "Adres"],
                    [[r["id"], r["ad_soyad"], r["telefon"], r["adres"]] for r in rows])
        else:
            rows = db.listele("SELECT urun, miktar, fiyat, kritik FROM parcalar ORDER BY urun")
            csv_yaz(klasor, "parcalar.csv", ["Parça", "Miktar", "Fiyat", "Kritik"],
                    [[r["urun"], r["miktar"], r["fiyat"], r["kritik"]] for r in rows])
        messagebox.showinfo("CSV", f"Dışa aktarıldı:\n{klasor}")


def main():
    secim = profil_secici()
    if not secim:
        return
    p = PROFILLER[secim]
    db = Veritabani(p["db"])
    ayar(db, "profil", secim)
    if durum(db)["kilitli"] and not kilit_goster(db):
        return
    App(db, p).mainloop()
