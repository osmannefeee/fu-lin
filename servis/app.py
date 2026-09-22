# -*- coding: utf-8 -*-
"""Teknik Servis Takip ana uygulama."""
import os
import tkinter as tk
import traceback
from datetime import date, timedelta
from tkinter import filedialog, messagebox, ttk

from . import SURUM
from .lisans import aktivasyon_formu, durum, kilit_goster
from .sabitler import (AD, ARIZALAR, CIHAZ_TURLERI, DURUMLAR, ISLEMLER, LISANS_TEL,
                       ODEME_YONTEM, RENK, SLOGAN, WA_NO)
from .veritabani import Veritabani, uygulama_dizini
from .yardim import ayar, bugun, csv_yaz, garanti_durumu, kayit_bakiye, musteri_sozluk, sms_metni, tl


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
        tk.Label(ust, text=f"  🛠️  {AD}", font=("Segoe UI", 15, "bold"),
                 bg="#0d1426", fg=RENK).pack(side="left", pady=10)
        tk.Label(ust, text=f"  {ayar(db, 'isletme')}  •  v{SURUM}", bg="#0d1426", fg="#93a1b8").pack(side="left")
        d = durum(db)
        self.lisans = d
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
        self.tp, self.tk_, self.tm, self.te, self.tg, self.tkasa, self.tr = (
            ttk.Frame(self.nb, padding=10) for _ in range(7))
        for f, b in [(self.tp, "📊 Panel"), (self.tk_, "🧾 Servis Kayıtları"), (self.tm, "👥 Müşteriler"),
                     (self.te, "👨‍🔧 Teknisyen & Stok"), (self.tg, "🛡️ Garanti"),
                     (self.tkasa, "💰 Kasa"), (self.tr, "✉️ SMS & Rapor")]:
            self.nb.add(f, text=f"  {b}  ")
        self.panel_kur()
        self.kayit_kur()
        self.mus_kur()
        self.ekip_kur()
        self.garanti_kur()
        self.kasa_kur()
        self.sms_kur()
        self.yenile()

    # ---------- iskelet ----------
    def _hata(self, exc, val, tb):
        try:
            with open(os.path.join(uygulama_dizini(), "servis_hata.log"), "a", encoding="utf-8") as f:
                f.write(f"\n===== {date.today()} =====\n")
                traceback.print_exception(exc, val, tb, file=f)
        except Exception:
            pass
        try:
            messagebox.showerror("Hata", f"İşlem yapılamadı:\n{val}\n\nDetay: servis_hata.log")
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
        t.tag_configure("warn", background="#fef9c3")
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
        for tablo in ["musteriler", "teknisyenler", "kayitlar", "parcalar", "kayit_parca",
                      "odemeler", "sms_log", "ayarlar"]:
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
        for i, (k, b) in enumerate([("ack", "🔧 Açık Kayıt"), ("haz", "✅ Hazır"), ("gar", "🛡️ Garanti Biten (30g)")]):
            f = tk.Frame(self.kart, bg=[RENK, "#0ea5e9", "#ef4444"][i])
            f.grid(row=0, column=i, padx=6, sticky="ew")
            self.kart.columnconfigure(i, weight=1)
            tk.Label(f, text=b, bg=f["bg"], fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
            v = tk.Label(f, text="0", bg=f["bg"], fg="white", font=("Segoe UI", 22, "bold"))
            v.pack(pady=(0, 12))
            self.deger[k] = v
        self.t_panel = self.agac(self.tp, [("no", "No", 60), ("m", "Müşteri", 200), ("c", "Cihaz", 220),
                                           ("d", "Durum", 130), ("b", "Kalan", 110)])

    # ---------- KAYITLAR ----------
    def kayit_kur(self):
        u = ttk.Frame(self.tk_)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Yeni Kayıt", command=self.kayit_form).pack(side="right", padx=3)
        ttk.Button(u, text="Durum Seç", command=self.durum_sec).pack(side="right", padx=3)
        ttk.Button(u, text="📄 Servis Formu", command=self.form_yazdir).pack(side="right", padx=3)
        ttk.Button(u, text="💵 Tahsilat", command=self.tahsilat).pack(side="right", padx=3)
        self.t_kayit = self.agac(self.tk_, [("id", "No", 55), ("m", "Müşteri", 170), ("c", "Cihaz", 200),
                                            ("a", "Arıza", 160), ("t", "Tutar", 100), ("d", "Durum", 120)])

    def secili_kayit(self):
        s = self.t_kayit.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM kayitlar WHERE id=?",
                               (self.t_kayit.item(s[0])["values"][0],))[0]

    def kayit_form(self, kayit=None):
        from .yardim import musteri_sozluk
        mus = musteri_sozluk(self.db)
        if not mus and not kayit:
            messagebox.showinfo("Bilgi", "Önce müşteri ekleyin.")
            return
        tekn = [r["ad"] for r in self.db.listele("SELECT * FROM teknisyenler WHERE aktif=1 ORDER BY ad")]
        w = tk.Toplevel(self)
        w.title("Servis Kaydı")
        w.geometry("440x640")
        ttk.Label(w, text="Müşteri *").pack(anchor="w", padx=12, pady=(8, 0))
        cm = ttk.Combobox(w, values=list(mus.keys()))
        cm.pack(padx=12, fill="x")
        ttk.Label(w, text="Cihaz Türü").pack(anchor="w", padx=12, pady=(8, 0))
        ct = ttk.Combobox(w, values=CIHAZ_TURLERI)
        ct.pack(padx=12, fill="x")
        ct.set(CIHAZ_TURLERI[0])
        alan = {}
        for et, k in [("Marka", "marka"), ("Model", "model"), ("Seri No", "seri")]:
            ttk.Label(w, text=et).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(w)
            e.pack(padx=12, fill="x")
            alan[k] = e
        ttk.Label(w, text="Arıza").pack(anchor="w", padx=12, pady=(8, 0))
        ca = ttk.Combobox(w, values=ARIZALAR)
        ca.pack(padx=12, fill="x")
        ttk.Label(w, text="Teknisyen").pack(anchor="w", padx=12, pady=(8, 0))
        ck = ttk.Combobox(w, values=tekn)
        ck.pack(padx=12, fill="x")
        if tekn:
            ck.set(tekn[0])
        ttk.Label(w, text="İşlem + Tutar").pack(anchor="w", padx=12, pady=(8, 0))
        fr = ttk.Frame(w)
        fr.pack(fill="x", padx=12)
        ci = ttk.Combobox(fr, values=list(ISLEMLER.keys()), width=26)
        ci.pack(side="left")
        ci.set(list(ISLEMLER.keys())[0])
        eu = ttk.Entry(fr, width=14)
        eu.pack(side="left", padx=6)
        eu.insert(0, str(list(ISLEMLER.values())[0]))
        ci.bind("<<ComboboxSelected>>",
                lambda e: (eu.delete(0, "end"), eu.insert(0, str(ISLEMLER.get(ci.get(), 0)))))
        ttk.Label(w, text="Garanti bitişi (YYYY-AA-GG, boş=yok)").pack(anchor="w", padx=12, pady=(8, 0))
        eg = ttk.Entry(w)
        eg.pack(padx=12, fill="x")
        if kayit:
            for k, e in alan.items():
                e.insert(0, kayit[k] or "")
            for cbx, v in [(ct, kayit["cihaz_tur"]), (ca, kayit["ariza"]), (ck, kayit["teknisyen"]), (ci, kayit["islem"])]:
                if v:
                    cbx.set(v)
            eu.delete(0, "end")
            eu.insert(0, str(kayit["tutar"] or 0))
            for m_, mid in mus.items():
                if mid == kayit["musteri_id"]:
                    cm.set(m_)
            if kayit["garanti_bitis"]:
                eg.insert(0, kayit["garanti_bitis"])

        def k():
            if not kayit and cm.get() not in mus:
                messagebox.showwarning("Uyarı", "Müşteri seçin.", parent=w)
                return
            try:
                tutar = float(eu.get() or 0)
            except ValueError:
                messagebox.showwarning("Uyarı", "Tutar sayısal olmalı.", parent=w)
                return
            gb = eg.get().strip()
            if gb:
                try:
                    date.fromisoformat(gb)
                except ValueError:
                    messagebox.showwarning("Uyarı", "Garanti tarihi YYYY-AA-GG olmalı.", parent=w)
                    return
            try:
                if kayit:
                    self.db.sorgu("""UPDATE kayitlar SET cihaz_tur=?,marka=?,model=?,seri=?,ariza=?,
                        teknisyen=?,islem=?,tutar=?,garanti_var=?,garanti_bitis=? WHERE id=?""",
                        (ct.get(), alan["marka"].get().strip(), alan["model"].get().strip(),
                         alan["seri"].get().strip(), ca.get(), ck.get(), ci.get(), tutar,
                         1 if gb else 0, gb or None, kayit["id"]))
                else:
                    self.db.sorgu("""INSERT INTO kayitlar
                        (musteri_id,cihaz_tur,marka,model,seri,ariza,islem,teknisyen,tutar,
                         garanti_var,garanti_bitis,durum,gelis)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (mus[cm.get()], ct.get(), alan["marka"].get().strip(), alan["model"].get().strip(),
                         alan["seri"].get().strip(), ca.get(), ci.get(), ck.get(), tutar,
                         1 if gb else 0, gb or None, "Alındı", bugun()))
            except Exception as ex:
                messagebox.showerror("Hata", f"Kayıt yazılamadı:\n{ex}", parent=w)
                return
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def durum_sec(self):
        e = self.secili_kayit()
        if not e:
            messagebox.showinfo("Bilgi", "Önce kayıt seçin.")
            return
        w = tk.Toplevel(self)
        w.title(f"Durum (Kayıt #{e['id']})")
        w.geometry("320x200")
        ttk.Label(w, text=f"Mevcut: {e['durum']}").pack(pady=8)
        cb = ttk.Combobox(w, values=DURUMLAR, state="readonly")
        cb.pack(padx=12, fill="x")
        cb.set(e["durum"])

        def uygula():
            self.db.sorgu("UPDATE kayitlar SET durum=?, teslim=? WHERE id=?",
                          (cb.get(), bugun() if cb.get() == "Teslim Edildi" else e["teslim"], e["id"]))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=uygula).pack(pady=12)

    def form_yazdir(self):
        import tempfile
        import webbrowser
        e = self.secili_kayit()
        if not e:
            messagebox.showinfo("Bilgi", "Önce kayıt seçin.")
            return
        m = self.db.listele("SELECT * FROM musteriler WHERE id=?", (e["musteri_id"],))[0]
        par = self.db.listele("SELECT * FROM kayit_parca WHERE kayit_id=?", (e["id"],))
        satir = "".join(f"<tr><td>{p['urun']}</td><td>{p['adet']}</td>"
                        f"<td>{(p['adet'] or 0) * (p['fiyat'] or 0):,.2f} ₺</td></tr>" for p in par)
        gar = f"Garanti bitişi: {e['garanti_bitis']}" if e["garanti_var"] else "Garanti dışı işlem"
        html = f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<title>Servis Formu #{e['id']}</title></head>
<body style="font-family:Arial;max-width:700px;margin:30px auto;color:#111">
<h2>{ayar(self.db, 'isletme')} — Servis Formu #{e['id']}</h2>
<p>Tarih: {e['gelis']} &nbsp; Durum: {e['durum']}</p><hr>
<p><b>Müşteri:</b> {m['ad_soyad']} — {m['telefon'] or ''}<br>
<b>Cihaz:</b> {e['cihaz_tur'] or ''} {e['marka'] or ''} {e['model'] or ''} (S/N: {e['seri'] or '-'})<br>
<b>Arıza:</b> {e['ariza'] or ''} &nbsp; <b>Teknisyen:</b> {e['teknisyen'] or ''}<br>
<b>{gar}</b></p>
<table border="1" cellpadding="8" cellspacing="0" width="100%">
<tr style="background:#eee"><th>İşlem/Parça</th><th>Adet</th><th>Tutar</th></tr>
<tr><td>{e['islem'] or ''}</td><td>1</td><td>{e['tutar'] or 0:,.2f} ₺</td></tr>{satir}
</table>
<p style="text-align:right"><b>TOPLAM: {e['tutar'] or 0:,.2f} ₺</b></p>
<br><br><table width="100%"><tr><td>Teslim Eden: ............</td><td>Teslim Alan: ............</td></tr></table>
</body></html>"""
        yol = os.path.join(tempfile.gettempdir(), f"servis_form_{e['id']}.html")
        with open(yol, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open("file://" + yol.replace("\\", "/"))

    def tahsilat(self):
        from .yardim import kayit_bakiye
        e = self.secili_kayit()
        if not e:
            return
        kalan, _, _ = kayit_bakiye(self.db, e["id"])
        w = tk.Toplevel(self)
        w.title(f"Tahsilat (#{e['id']})")
        w.geometry("320x280")
        ttk.Label(w, text=f"Kalan borç: {tl(kalan)}", font=("Segoe UI", 11, "bold")).pack(pady=8)
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
            self.db.sorgu("INSERT INTO odemeler(kayit_id,musteri_id,tarih,tutar,yontem) VALUES(?,?,?,?,?)",
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
                                         ("is", "Kayıt", 80), ("borc", "Borç", 110)])
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
        return self.db.listele("SELECT * FROM musteriler WHERE id=?",
                               (self.t_mus.item(s[0])["values"][0],))[0]

    def mus_duzenle(self):
        k = self.secili_mus()
        if k:
            self.mus_form(k)

    # ---------- TEKNİSYEN & STOK ----------
    def ekip_kur(self):
        sol = ttk.LabelFrame(self.te, text="👨‍🔧 Teknisyenler")
        sol.pack(side="left", fill="both", expand=True, padx=4)
        sag = ttk.LabelFrame(self.te, text="🔩 Parça Stoku")
        sag.pack(side="left", fill="both", expand=True, padx=4)
        ttk.Button(sol, text="+ Teknisyen", command=self.teknisyen_form).pack(anchor="e")
        self.t_tek = self.agac(sol, [("id", "ID", 40), ("ad", "Ad", 180), ("is", "Aktif İş", 80)])
        bar = ttk.Frame(sag)
        bar.pack(fill="x")
        ttk.Button(bar, text="+ Parça", command=self.parca_form).pack(side="right", padx=3)
        ttk.Button(bar, text="+/-", command=self.parca_hareket).pack(side="right", padx=3)
        self.t_par = self.agac(sag, [("id", "ID", 40), ("u", "Parça", 180), ("m", "Miktar", 70), ("f", "Fiyat", 100)])

    def teknisyen_form(self):
        w = tk.Toplevel(self)
        w.title("Teknisyen")
        w.geometry("320x220")
        ttk.Label(w, text="Ad *").pack(anchor="w", padx=12, pady=(8, 0))
        ea = ttk.Entry(w)
        ea.pack(padx=12, fill="x")
        ttk.Label(w, text="Telefon").pack(anchor="w", padx=12, pady=(8, 0))
        et = ttk.Entry(w)
        et.pack(padx=12, fill="x")

        def k():
            if ea.get().strip():
                self.db.sorgu("INSERT INTO teknisyenler(ad,telefon) VALUES(?,?)",
                              (ea.get().strip(), et.get().strip()))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=10)

    def parca_form(self):
        w = tk.Toplevel(self)
        w.title("Parça")
        w.geometry("320x260")
        ttk.Label(w, text="Parça adı *").pack(anchor="w", padx=12, pady=(8, 0))
        eu = ttk.Entry(w)
        eu.pack(padx=12, fill="x")
        ttk.Label(w, text="Fiyat").pack(anchor="w", padx=12, pady=(8, 0))
        ef = ttk.Entry(w)
        ef.pack(padx=12, fill="x")
        ef.insert(0, "0")

        def k():
            if eu.get().strip():
                try:
                    f = float(ef.get() or 0)
                except ValueError:
                    f = 0
                self.db.sorgu("INSERT OR IGNORE INTO parcalar(urun,fiyat) VALUES(?,?)",
                              (eu.get().strip(), f))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=10)

    def parca_hareket(self):
        s = self.t_par.selection()
        if not s:
            return
        sid = self.t_par.item(s[0])["values"][0]
        w = tk.Toplevel(self)
        w.title("Stok")
        w.geometry("260x160")
        ttk.Label(w, text="Miktar (+/-):").pack(pady=8)
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

    # ---------- GARANTİ ----------
    def garanti_kur(self):
        ttk.Label(self.tg, text="30 gün içinde biten + bitmiş garantiler", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.t_gar = self.agac(self.tg, [("id", "No", 55), ("m", "Müşteri", 180), ("c", "Cihaz", 200),
                                         ("b", "Bitiş", 110), ("k", "Kalan", 100)])

    # ---------- KASA ----------
    def kasa_kur(self):
        self.kasa_ozet = ttk.Label(self.tkasa, text="", font=("Segoe UI", 12, "bold"))
        self.kasa_ozet.pack(anchor="w", pady=4)
        self.t_kasa = self.agac(self.tkasa, [("t", "Tarih", 100), ("k", "Kayıt", 70), ("m", "Müşteri", 200),
                                             ("u", "Tutar", 120), ("y", "Yöntem", 120)])

    # ---------- SMS & RAPOR ----------
    def sms_kur(self):
        u = ttk.Frame(self.tr)
        u.pack(fill="x", pady=4)
        ttk.Label(u, text="'Hazır' kayıtlara SMS bildir").pack(side="left")
        ttk.Button(u, text="✉️ SMS Hazırla", command=self.sms_hazir).pack(side="right", padx=3)
        self.sms_txt = tk.Text(self.tr, height=7, font=("Segoe UI", 10))
        self.sms_txt.pack(fill="x", pady=4)
        bar = ttk.Frame(self.tr)
        bar.pack(fill="x", pady=2)
        ttk.Label(bar, text="📈 Rapor", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(bar, text="⬇ CSV: Kayıtlar", command=lambda: self.rapor_csv("kay")).pack(side="right", padx=3)
        ttk.Button(bar, text="⬇ CSV: Kasa", command=lambda: self.rapor_csv("kas")).pack(side="right", padx=3)
        self.rapor_txt = tk.Text(self.tr, height=9, font=("Consolas", 10), bg="#0d1426", fg="#a7f3d0")
        self.rapor_txt.pack(fill="both", expand=True)

    def sms_hazir(self):
        from .yardim import sms_metni
        rows = self.db.listele("""SELECT k.id, m.ad_soyad ad, m.telefon tel, k.durum FROM kayitlar k
            LEFT JOIN musteriler m ON m.id=k.musteri_id WHERE k.durum='Hazır' ORDER BY k.id DESC LIMIT 50""")
        self.sms_txt.delete("1.0", "end")
        if not rows:
            self.sms_txt.insert("1.0", "'Hazır' kaydı yok.")
            return
        for r in rows:
            m = sms_metni(self.db, r["ad"], f"#{r['id']}", r["durum"])
            self.db.sorgu("INSERT INTO sms_log(tarih,telefon,mesaj,durum) VALUES(?,?,?,?)",
                          (bugun(), r["tel"], m, "Hazırlandı"))
            self.sms_txt.insert("end", f"📱 {r['tel']} → {m}\n\n")
        self.clipboard_clear()
        self.clipboard_append(self.sms_txt.get("1.0", "end").strip())
        messagebox.showinfo("SMS", f"{len(rows)} mesaj hazır, kopyalandı.")

    def rapor_csv(self, tur):
        klasor = filedialog.askdirectory(title="CSV klasörü")
        if not klasor:
            return
        db = self.db
        if tur == "kay":
            rows = db.listele("""SELECT k.id, m.ad_soyad, m.telefon, k.cihaz_tur, k.marka, k.model,
                k.ariza, k.tutar, k.durum, k.gelis, k.teslim FROM kayitlar k
                LEFT JOIN musteriler m ON m.id=k.musteri_id ORDER BY k.id DESC""")
            csv_yaz(klasor, "servis_kayitlari.csv",
                    ["No", "Müşteri", "Telefon", "Cihaz", "Marka", "Model", "Arıza",
                     "Tutar", "Durum", "Geliş", "Teslim"],
                    [[r["id"], r["ad_soyad"], r["telefon"], r["cihaz_tur"], r["marka"], r["model"],
                      r["ariza"], r["tutar"], r["durum"], r["gelis"], r["teslim"]] for r in rows])
        else:
            rows = db.listele("""SELECT o.tarih, o.kayit_id, m.ad_soyad, o.tutar, o.yontem FROM odemeler o
                LEFT JOIN musteriler m ON m.id=o.musteri_id ORDER BY o.id DESC""")
            csv_yaz(klasor, "kasa.csv", ["Tarih", "Kayıt", "Müşteri", "Tutar", "Yöntem"],
                    [[r["tarih"], r["kayit_id"], r["ad_soyad"], r["tutar"], r["yontem"]] for r in rows])
        messagebox.showinfo("CSV", f"Dışa aktarıldı:\n{klasor}")

    # ---------- YENİLE ----------
    def yenile(self):
        from .yardim import kayit_bakiye
        db = self.db
        ay = date.today().strftime("%Y-%m")
        ack = db.listele("SELECT COUNT(*) s FROM kayitlar WHERE durum NOT IN ('Teslim Edildi','İptal')")[0]["s"]
        haz = db.listele("SELECT COUNT(*) s FROM kayitlar WHERE durum='Hazır'")[0]["s"]
        gb = sum(1 for r in db.listele("SELECT garanti_bitis FROM kayitlar WHERE garanti_var=1 AND garanti_bitis<>''")
                 if garanti_durumu(r["garanti_bitis"])[0] in ("bitmis", "yaklasiyor"))
        self.deger["ack"].config(text=str(ack))
        self.deger["haz"].config(text=str(haz))
        self.deger["gar"].config(text=str(gb))
        for t in (self.t_panel, self.t_kayit, self.t_mus, self.t_tek, self.t_par, self.t_gar, self.t_kasa):
            for i in t.get_children():
                t.delete(i)
        i = 0
        for r in db.listele("""SELECT k.id, m.ad_soyad ad, k.marka, k.model, k.durum
            FROM kayitlar k LEFT JOIN musteriler m ON m.id=k.musteri_id
            WHERE k.durum NOT IN ('Teslim Edildi','İptal') ORDER BY k.id DESC LIMIT 100"""):
            kalan, _, _ = kayit_bakiye(db, r["id"])
            self.satir(self.t_panel, i, (r["id"], r["ad"], f"{r['marka'] or ''} {r['model'] or ''}",
                                         r["durum"], tl(kalan)), "ok" if r["durum"] == "Hazır" else "")
            i += 1
        i = 0
        for r in db.listele("""SELECT k.*, m.ad_soyad ad FROM kayitlar k
            LEFT JOIN musteriler m ON m.id=k.musteri_id ORDER BY k.id DESC LIMIT 300"""):
            tag = "ok" if r["durum"] in ("Hazır", "Teslim Edildi") else \
                ("kritik" if r["durum"] == "İptal" else ("even" if i % 2 else "odd"))
            self.satir(self.t_kayit, i, (r["id"], r["ad"], f"{r['marka'] or ''} {r['model'] or ''}",
                                         r["ariza"], tl(r["tutar"]), r["durum"]), tag)
            i += 1
        q = (self.mq.get() or "").strip()
        rows = db.listele("SELECT * FROM musteriler WHERE ad_soyad LIKE ? OR telefon LIKE ? ORDER BY ad_soyad",
                          (f"%{q}%", f"%{q}%")) if q else db.listele("SELECT * FROM musteriler ORDER BY ad_soyad LIMIT 400")
        for j, m in enumerate(rows):
            nis = db.listele("SELECT COUNT(*) s FROM kayitlar WHERE musteri_id=?", (m["id"],))[0]["s"]
            borc = db.listele("""SELECT COALESCE(SUM(k.tutar),0)-COALESCE(
                (SELECT SUM(tutar) FROM odemeler o WHERE o.musteri_id=k.musteri_id),0) b
                FROM kayitlar k WHERE k.musteri_id=?""", (m["id"],))[0]["b"] or 0
            self.satir(self.t_mus, j, (m["id"], m["ad_soyad"], m["telefon"], nis, tl(borc)),
                       "kritik" if borc > 0.5 else "")
        for j, r in enumerate(db.listele("SELECT * FROM teknisyenler ORDER BY ad")):
            aktif = db.listele("SELECT COUNT(*) s FROM kayitlar WHERE teknisyen=? AND durum NOT IN ('Teslim Edildi','İptal')",
                               (r["ad"],))[0]["s"]
            self.satir(self.t_tek, j, (r["id"], r["ad"], aktif))
        for j, r in enumerate(db.listele("SELECT * FROM parcalar ORDER BY urun")):
            self.satir(self.t_par, j, (r["id"], r["urun"], r["miktar"], tl(r["fiyat"])),
                       "kritik" if (r["miktar"] or 0) <= (r["kritik"] or 0) else "")
        gi = 0
        for r in db.listele("""SELECT k.id, m.ad_soyad ad, k.marka, k.model, k.garanti_bitis
            FROM kayitlar k LEFT JOIN musteriler m ON m.id=k.musteri_id
            WHERE k.garanti_var=1 AND k.garanti_bitis<>'' ORDER BY k.garanti_bitis"""):
            g, gun = garanti_durumu(r["garanti_bitis"])
            if g == "yok":
                continue
            tag = "kritik" if g == "bitmis" else ("warn" if g == "yaklasiyor" else "")
            kalan_m = "bitti" if g == "bitmis" else f"{gun} gün"
            self.satir(self.t_gar, gi, (r["id"], r["ad"], f"{r['marka'] or ''} {r['model'] or ''}",
                                        r["garanti_bitis"], kalan_m), tag)
            gi += 1
        ciro = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler WHERE substr(tarih,1,7)=?", (ay,))[0]["s"] or 0
        tah = 0
        for j, r in enumerate(db.listele("""SELECT o.tarih, o.kayit_id, m.ad_soyad, o.tutar, o.yontem
            FROM odemeler o LEFT JOIN musteriler m ON m.id=o.musteri_id ORDER BY o.id DESC LIMIT 200""")):
            self.satir(self.t_kasa, j, (r["tarih"], f"#{r['kayit_id']}" if r["kayit_id"] else "-", r["ad_soyad"],
                                        tl(r["tutar"]), r["yontem"]))
            tah += r["tutar"] or 0
        self.kasa_ozet.config(text=f"Toplam tahsilat: {tl(tah)}  |  Bu ay: {tl(ciro)}")
        nis = db.listele("SELECT COUNT(*) s FROM kayitlar WHERE substr(gelis,1,7)=?", (ay,))[0]["s"]
        sat = [f"===== {ay} SERVİS RAPORU =====", f"Alınan kayıt: {nis}", f"Tahsilat: {tl(ciro)}", "",
               "--- Durum Dağılımı ---"]
        for r in db.listele("SELECT durum, COUNT(*) n FROM kayitlar GROUP BY durum"):
            sat.append(f"{r['durum']}: {r['n']}")
        sat.append("")
        sat.append("--- Cihaz Türü Bazında ---")
        for r in db.listele("""SELECT cihaz_tur, COUNT(*) n, COALESCE(SUM(tutar),0) t FROM kayitlar
            WHERE substr(gelis,1,7)=? GROUP BY cihaz_tur ORDER BY t DESC""", (ay,)):
            sat.append(f"{r['cihaz_tur'] or '?'}: {r['n']} kayıt, {tl(r['t'])}")
        sat.append("")
        sat.append("--- Teknisyen Performansı (ay) ---")
        for r in db.listele("""SELECT teknisyen, COUNT(*) n FROM kayitlar
            WHERE substr(gelis,1,7)=? GROUP BY teknisyen ORDER BY n DESC""", (ay,)):
            sat.append(f"{r['teknisyen'] or '?'}: {r['n']} kayıt")
        self.rapor_txt.delete("1.0", "end")
        self.rapor_txt.insert("1.0", "\n".join(sat))


def main():
    db = Veritabani()
    if durum(db)["kilitli"] and not kilit_goster(db):
        return
    App(db).mainloop()
