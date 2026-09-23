# -*- coding: utf-8 -*-
"""CrmPro ana uygulama."""
import os
import tkinter as tk
import traceback
from datetime import date
from tkinter import filedialog, messagebox, ttk

from . import SURUM
from .lisans import aktivasyon_formu, durum, kilit_goster
from .sabitler import (AD, AKTIVITE_TUR, ASAMA_OLASILIK, ASAMALAR, GOREV_DURUM,
                       KAYNAKLAR, LISANS_TEL, RENK, SLOGAN, TEKLIF_DURUM, WA_NO)
from .veritabani import Veritabani, uygulama_dizini
from .yardim import (agirlikli_ciro, ayar, bugun, csv_yaz, musteri_sozluk,
                     teklif_no_uret, teklif_toplam, tl, vade_yakin_mi)


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
        tk.Label(ust, text=f"  📇  {AD}", font=("Segoe UI", 15, "bold"),
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
        self.tp, self.tf, self.tm, self.ta, self.tt, self.tg, self.tr = (
            ttk.Frame(self.nb, padding=10) for _ in range(7))
        for f, b in [(self.tp, "📊 Panel"), (self.tf, "🎯 Fırsatlar"), (self.tm, "👥 Müşteriler"),
                     (self.ta, "📞 Aktiviteler"), (self.tt, "📝 Teklifler"),
                     (self.tg, "✅ Görevler"), (self.tr, "✉️ SMS & Rapor")]:
            self.nb.add(f, text=f"  {b}  ")
        self.panel_kur()
        self.firsat_kur()
        self.mus_kur()
        self.akt_kur()
        self.teklif_kur()
        self.gorev_kur()
        self.sms_kur()
        self.yenile()

    # ---------- iskelet ----------
    def _hata(self, exc, val, tb):
        try:
            with open(os.path.join(uygulama_dizini(), "crm_hata.log"), "a", encoding="utf-8") as f:
                f.write(f"\n===== {date.today()} =====\n")
                traceback.print_exception(exc, val, tb, file=f)
        except Exception:
            pass
        try:
            messagebox.showerror("Hata", f"İşlem yapılamadı:\n{val}\n\nDetay: crm_hata.log")
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
        for tablo in ["musteriler", "firsatlar", "aktiviteler", "teklifler", "teklif_kalem",
                      "gorevler", "sms_log", "ayarlar"]:
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
        for i, (k, b) in enumerate([("frs", "🎯 Açık Fırsat"), ("agr", "💰 Ağırlıklı Ciro"),
                                    ("tkp", "⏰ Yaklaşan Takip")]):
            f = tk.Frame(self.kart, bg=[RENK, "#0ea5e9", "#f59e0b"][i])
            f.grid(row=0, column=i, padx=6, sticky="ew")
            self.kart.columnconfigure(i, weight=1)
            tk.Label(f, text=b, bg=f["bg"], fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(10, 0))
            v = tk.Label(f, text="0", bg=f["bg"], fg="white", font=("Segoe UI", 22, "bold"))
            v.pack(pady=(0, 12))
            self.deger[k] = v
        alt = ttk.Frame(self.tp)
        alt.pack(fill="both", expand=True, pady=6)
        s1 = ttk.LabelFrame(alt, text="🔥 Sıcak Fırsatlar (teklif+)")
        s1.pack(side="left", fill="both", expand=True, padx=4)
        s2 = ttk.LabelFrame(alt, text="⏰ Bugünkü Takipler")
        s2.pack(side="left", fill="both", expand=True, padx=4)
        self.t_sicak = self.agac(s1, [("b", "Fırsat", 200), ("m", "Müşteri", 170), ("t", "Tutar", 110)])
        self.t_takip = self.agac(s2, [("t", "Tür", 90), ("m", "Müşteri", 170), ("o", "Özet", 200)])

    # ---------- FIRSATLAR ----------
    def firsat_kur(self):
        u = ttk.Frame(self.tf)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Fırsat", command=self.firsat_form).pack(side="right", padx=3)
        ttk.Button(u, text="Aşama Seç", command=self.firsat_asama).pack(side="right", padx=3)
        ttk.Button(u, text="Sil", command=self.firsat_sil).pack(side="right", padx=3)
        self.t_firsat = self.agac(self.tf, [("id", "ID", 45), ("b", "Fırsat", 220), ("m", "Müşteri", 180),
                                            ("t", "Tutar", 110), ("o", "%", 55), ("a", "Aşama", 110)])

    def secili_firsat(self):
        s = self.t_firsat.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM firsatlar WHERE id=?",
                               (self.t_firsat.item(s[0])["values"][0],))[0]

    def firsat_form(self, kayit=None):
        mus = musteri_sozluk(self.db)
        if not mus and not kayit:
            messagebox.showinfo("Bilgi", "Önce müşteri ekleyin.")
            return
        w = tk.Toplevel(self)
        w.title("Fırsat")
        w.geometry("380x420")
        ttk.Label(w, text="Müşteri *").pack(anchor="w", padx=12, pady=(8, 0))
        cm = ttk.Combobox(w, values=list(mus.keys()))
        cm.pack(padx=12, fill="x")
        ttk.Label(w, text="Fırsat başlığı *").pack(anchor="w", padx=12, pady=(8, 0))
        eb = ttk.Entry(w)
        eb.pack(padx=12, fill="x")
        ttk.Label(w, text="Tutar (TL)").pack(anchor="w", padx=12, pady=(8, 0))
        et = ttk.Entry(w)
        et.pack(padx=12, fill="x")
        et.insert(0, "0")
        ttk.Label(w, text="Aşama").pack(anchor="w", padx=12, pady=(8, 0))
        ca = ttk.Combobox(w, values=ASAMALAR, state="readonly")
        ca.pack(padx=12, fill="x")
        ca.set("Aday")
        ttk.Label(w, text="Not").pack(anchor="w", padx=12, pady=(8, 0))
        en = ttk.Entry(w)
        en.pack(padx=12, fill="x")
        if kayit:
            for m_, mid in mus.items():
                if mid == kayit["musteri_id"]:
                    cm.set(m_)
            eb.insert(0, kayit["baslik"] or "")
            et.delete(0, "end")
            et.insert(0, str(kayit["tutar"] or 0))
            ca.set(kayit["asama"])
            en.insert(0, kayit["notlar"] or "")

        def k():
            if not kayit and cm.get() not in mus:
                messagebox.showwarning("Uyarı", "Müşteri seçin.", parent=w)
                return
            if not eb.get().strip():
                messagebox.showwarning("Uyarı", "Başlık gerekli.", parent=w)
                return
            try:
                tutar = float(et.get() or 0)
            except ValueError:
                messagebox.showwarning("Uyarı", "Tutar sayısal olmalı.", parent=w)
                return
            try:
                if kayit:
                    self.db.sorgu("UPDATE firsatlar SET baslik=?,tutar=?,asama=?,olasilik=?,notlar=? WHERE id=?",
                                  (eb.get().strip(), tutar, ca.get(), ASAMA_OLASILIK.get(ca.get(), 10),
                                   en.get().strip(), kayit["id"]))
                else:
                    self.db.sorgu("""INSERT INTO firsatlar(musteri_id,baslik,tutar,asama,olasilik,notlar)
                                     VALUES(?,?,?,?,?,?)""",
                                  (mus[cm.get()], eb.get().strip(), tutar, ca.get(),
                                   ASAMA_OLASILIK.get(ca.get(), 10), en.get().strip()))
            except Exception as ex:
                messagebox.showerror("Hata", f"Kaydedilemedi:\n{ex}", parent=w)
                return
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def firsat_asama(self):
        f = self.secili_firsat()
        if not f:
            messagebox.showinfo("Bilgi", "Önce fırsat seçin.")
            return
        w = tk.Toplevel(self)
        w.title(f"Aşama (#{f['id']})")
        w.geometry("300x190")
        ttk.Label(w, text=f"Mevcut: {f['asama']}").pack(pady=8)
        cb = ttk.Combobox(w, values=ASAMALAR, state="readonly")
        cb.pack(padx=12, fill="x")
        cb.set(f["asama"])

        def uygula():
            self.db.sorgu("UPDATE firsatlar SET asama=?, olasilik=? WHERE id=?",
                          (cb.get(), ASAMA_OLASILIK.get(cb.get(), 10), f["id"]))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=uygula).pack(pady=12)

    def firsat_sil(self):
        f = self.secili_firsat()
        if f and messagebox.askyesno("Onay", "Fırsat silinsin mi?"):
            self.db.sorgu("DELETE FROM firsatlar WHERE id=?", (f["id"],))
            self.yenile()

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
        ttk.Button(u, text="Sil", command=self.mus_sil).pack(side="right", padx=4)
        self.t_mus = self.agac(self.tm, [("id", "ID", 45), ("f", "Firma", 200), ("y", "Yetkili", 150),
                                         ("t", "Telefon", 130), ("k", "Kaynak", 110)])
        self.t_mus.bind("<Double-1>", lambda e: self.mus_duzenle())

    def mus_form(self, kayit=None):
        w = tk.Toplevel(self)
        w.title("Müşteri")
        w.geometry("380x480")
        alan = {}
        for et, k in [("Firma *", "firma"), ("Yetkili", "yetkili"), ("Telefon", "tel"),
                      ("E-posta", "eposta"), ("Adres", "adres"), ("Etiket", "etiket"), ("Notlar", "not")]:
            ttk.Label(w, text=et).pack(anchor="w", padx=12, pady=(6, 0))
            if k == "kaynak":
                continue
            e = ttk.Entry(w)
            e.pack(padx=12, fill="x")
            alan[k] = e
        ttk.Label(w, text="Kaynak").pack(anchor="w", padx=12, pady=(6, 0))
        ck = ttk.Combobox(w, values=KAYNAKLAR)
        ck.pack(padx=12, fill="x")
        ck.set("Web Sitesi")
        if kayit:
            for k, e in alan.items():
                e.insert(0, {"firma": kayit["firma"], "yetkili": kayit["yetkili"], "tel": kayit["telefon"],
                             "eposta": kayit["eposta"], "adres": kayit["adres"],
                             "etiket": kayit["etiket"], "not": kayit["notlar"]}[k] or "")
            ck.set(kayit["kaynak"] or "Web Sitesi")

        def k():
            if not alan["firma"].get().strip() and not alan["yetkili"].get().strip():
                messagebox.showwarning("Uyarı", "Firma veya yetkili gerekli.", parent=w)
                return
            v = [alan[x].get().strip() for x in ("firma", "yetkili", "tel", "eposta", "adres", "etiket", "not")]
            try:
                if kayit:
                    self.db.sorgu("""UPDATE musteriler SET firma=?,yetkili=?,telefon=?,eposta=?,
                        adres=?,etiket=?,notlar=?,kaynak=? WHERE id=?""", (*v, ck.get(), kayit["id"]))
                else:
                    self.db.sorgu("""INSERT INTO musteriler
                        (firma,yetkili,telefon,eposta,adres,etiket,notlar,kaynak) VALUES(?,?,?,?,?,?,?,?)""",
                        (*v, ck.get()))
            except Exception as ex:
                messagebox.showerror("Hata", f"Kaydedilemedi:\n{ex}", parent=w)
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

    def mus_sil(self):
        k = self.secili_mus()
        if k and messagebox.askyesno("Onay", "Müşteri ve bağlantılı kayıtlar silinsin mi?"):
            for t, kol in (("aktiviteler", "musteri_id"), ("firsatlar", "musteri_id"),
                           ("teklifler", "musteri_id"), ("gorevler", "musteri_id")):
                self.db.sorgu(f"DELETE FROM {t} WHERE {kol}=?", (k["id"],))
            self.db.sorgu("DELETE FROM musteriler WHERE id=?", (k["id"],))
            self.yenile()

    # ---------- AKTİVİTELER ----------
    def akt_kur(self):
        u = ttk.Frame(self.ta)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Görüşme Ekle", command=self.akt_form).pack(side="right", padx=3)
        ttk.Button(u, text="Sil", command=self.akt_sil).pack(side="right", padx=3)
        self.t_akt = self.agac(self.ta, [("id", "ID", 40), ("t", "Tarih", 100), ("u", "Tür", 90),
                                         ("m", "Müşteri", 180), ("o", "Özet", 220), ("s", "Sonraki Takip", 110)])

    def akt_form(self):
        mus = musteri_sozluk(self.db)
        if not mus:
            messagebox.showinfo("Bilgi", "Önce müşteri ekleyin.")
            return
        w = tk.Toplevel(self)
        w.title("Görüşme")
        w.geometry("380x440")
        ttk.Label(w, text="Müşteri *").pack(anchor="w", padx=12, pady=(8, 0))
        cm = ttk.Combobox(w, values=list(mus.keys()))
        cm.pack(padx=12, fill="x")
        ttk.Label(w, text="Tür").pack(anchor="w", padx=12, pady=(8, 0))
        ct = ttk.Combobox(w, values=AKTIVITE_TUR, state="readonly")
        ct.pack(padx=12, fill="x")
        ct.set("Telefon")
        ttk.Label(w, text="Tarih").pack(anchor="w", padx=12, pady=(8, 0))
        et = ttk.Entry(w)
        et.pack(padx=12, fill="x")
        et.insert(0, bugun())
        ttk.Label(w, text="Özet *").pack(anchor="w", padx=12, pady=(8, 0))
        eo = ttk.Entry(w)
        eo.pack(padx=12, fill="x")
        ttk.Label(w, text="Sonuç").pack(anchor="w", padx=12, pady=(8, 0))
        es = ttk.Entry(w)
        es.pack(padx=12, fill="x")
        ttk.Label(w, text="Sonraki takip (YYYY-AA-GG)").pack(anchor="w", padx=12, pady=(8, 0))
        ef = ttk.Entry(w)
        ef.pack(padx=12, fill="x")

        def k():
            if cm.get() not in mus or not eo.get().strip():
                messagebox.showwarning("Uyarı", "Müşteri ve özet gerekli.", parent=w)
                return
            self.db.sorgu("""INSERT INTO aktiviteler(musteri_id,tur,tarih,ozet,sonuc,takip)
                             VALUES(?,?,?,?,?,?)""",
                          (mus[cm.get()], ct.get(), et.get().strip(), eo.get().strip(),
                           es.get().strip(), ef.get().strip() or None))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def akt_sil(self):
        s = self.t_akt.selection()
        if s and messagebox.askyesno("Onay", "Kayıt silinsin mi?"):
            self.db.sorgu("DELETE FROM aktiviteler WHERE id=?", (self.t_akt.item(s[0])["values"][0],))
            self.yenile()

    # ---------- TEKLİFLER ----------
    def teklif_kur(self):
        u = ttk.Frame(self.tt)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Teklif", command=self.teklif_form).pack(side="right", padx=3)
        ttk.Button(u, text="Durum", command=self.teklif_durum).pack(side="right", padx=3)
        ttk.Button(u, text="🖨️ Yazdır", command=self.teklif_yazdir).pack(side="right", padx=3)
        ttk.Button(u, text="Sil", command=self.teklif_sil).pack(side="right", padx=3)
        self.t_tek = self.agac(self.tt, [("id", "ID", 40), ("no", "No", 110), ("m", "Müşteri", 180),
                                         ("t", "Toplam", 120), ("d", "Durum", 100)])

    def secili_teklif(self):
        s = self.t_tek.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM teklifler WHERE id=?",
                               (self.t_tek.item(s[0])["values"][0],))[0]

    def teklif_form(self):
        mus = musteri_sozluk(self.db)
        if not mus:
            messagebox.showinfo("Bilgi", "Önce müşteri ekleyin.")
            return
        w = tk.Toplevel(self)
        w.title("Teklif")
        w.geometry("460x560")
        ttk.Label(w, text="Müşteri *").pack(anchor="w", padx=12, pady=(8, 0))
        cm = ttk.Combobox(w, values=list(mus.keys()))
        cm.pack(padx=12, fill="x")
        fr = ttk.Frame(w)
        fr.pack(fill="x", padx=12, pady=6)
        ttk.Label(fr, text="KDV %:").pack(side="left")
        ek = ttk.Entry(fr, width=8)
        ek.pack(side="left", padx=4)
        ek.insert(0, "20")
        ttk.Label(fr, text="Kalemler:").pack(side="left", padx=(10, 0))
        ttk.Button(fr, text="+ Kalem", command=lambda: kalem_ekle()).pack(side="right")
        lst = tk.Listbox(w, height=8)
        lst.pack(padx=12, fill="both", expand=True)
        kalemler = []

        def kalem_ekle():
            k = tk.Toplevel(w)
            k.title("Kalem")
            k.geometry("320x240")
            ttk.Label(k, text="Açıklama").pack(anchor="w", padx=10, pady=(8, 0))
            ea = ttk.Entry(k)
            ea.pack(padx=10, fill="x")
            ttk.Label(k, text="Adet").pack(anchor="w", padx=10, pady=(8, 0))
            ed = ttk.Entry(k)
            ed.pack(padx=10, fill="x")
            ed.insert(0, "1")
            ttk.Label(k, text="Birim fiyat").pack(anchor="w", padx=10, pady=(8, 0))
            ef = ttk.Entry(k)
            ef.pack(padx=10, fill="x")
            ef.insert(0, "0")

            def ekle():
                try:
                    ad, fi = float(ed.get() or 1), float(ef.get() or 0)
                except ValueError:
                    messagebox.showwarning("Uyarı", "Sayısal girin.", parent=k)
                    return
                kalemler.append((ea.get().strip() or "Kalem", ad, fi))
                lst.insert("end", f"{kalemler[-1][0]} — {ad:g} x {tl(fi)}")
                k.destroy()

            ttk.Button(k, text="Ekle", command=ekle).pack(pady=10)

        ttk.Label(w, text="Not").pack(anchor="w", padx=12)
        en = ttk.Entry(w)
        en.pack(padx=12, fill="x")

        def k():
            if cm.get() not in mus:
                messagebox.showwarning("Uyarı", "Müşteri seçin.", parent=w)
                return
            if not kalemler:
                messagebox.showwarning("Uyarı", "En az bir kalem ekleyin.", parent=w)
                return
            try:
                oran = float(ek.get() or 20)
            except ValueError:
                oran = 20
            no = teklif_no_uret(self.db)
            cur = self.db.sorgu("""INSERT INTO teklifler(musteri_id,no,tarih,kdv_oran,notlar)
                                   VALUES(?,?,?,?,?)""",
                                (mus[cm.get()], no, bugun(), oran, en.get().strip()))
            tid = cur.lastrowid
            for a, ad, fi in kalemler:
                self.db.sorgu("INSERT INTO teklif_kalem(teklif_id,aciklama,adet,fiyat) VALUES(?,?,?,?)",
                              (tid, a, ad, fi))
            w.destroy()
            self.yenile()
            messagebox.showinfo("Teklif", f"{no} oluşturuldu.")

        ttk.Button(w, text="Teklifi Kaydet", command=k).pack(pady=10)

    def teklif_durum(self):
        t = self.secili_teklif()
        if not t:
            return
        w = tk.Toplevel(self)
        w.title("Teklif Durumu")
        w.geometry("280x170")
        cb = ttk.Combobox(w, values=TEKLIF_DURUM, state="readonly")
        cb.pack(padx=12, pady=12, fill="x")
        cb.set(t["durum"])

        def uygula():
            self.db.sorgu("UPDATE teklifler SET durum=? WHERE id=?", (cb.get(), t["id"]))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=uygula).pack()

    def teklif_sil(self):
        t = self.secili_teklif()
        if t and messagebox.askyesno("Onay", "Teklif silinsin mi?"):
            self.db.sorgu("DELETE FROM teklif_kalem WHERE teklif_id=?", (t["id"],))
            self.db.sorgu("DELETE FROM teklifler WHERE id=?", (t["id"],))
            self.yenile()

    def teklif_yazdir(self):
        import tempfile
        import webbrowser
        t = self.secili_teklif()
        if not t:
            return
        m = self.db.listele("SELECT * FROM musteriler WHERE id=?", (t["musteri_id"],))[0]
        kal = self.db.listele("SELECT * FROM teklif_kalem WHERE teklif_id=?", (t["id"],))
        ara, kdv, genel = teklif_toplam(self.db, t["id"])
        sat = "".join(f"<tr><td>{k['aciklama']}</td><td>{k['adet']:g}</td>"
                      f"<td>{k['fiyat']:,.2f} ₺</td><td>{(k['adet'] or 0) * (k['fiyat'] or 0):,.2f} ₺</td></tr>"
                      for k in kal)
        html = f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<title>Teklif {t['no']}</title></head>
<body style="font-family:Arial;max-width:700px;margin:30px auto;color:#111">
<h2>{ayar(self.db, 'isletme')} — Teklif {t['no']}</h2>
<p>Tarih: {t['tarih']} &nbsp; Durum: {t['durum']}</p><hr>
<p><b>Müşteri:</b> {m['firma'] or ''} / {m['yetkili'] or ''} — {m['telefon'] or ''}</p>
<table border="1" cellpadding="8" cellspacing="0" width="100%">
<tr style="background:#eee"><th>Açıklama</th><th>Adet</th><th>Birim</th><th>Tutar</th></tr>{sat}
</table>
<p style="text-align:right">Ara: {ara:,.2f} ₺<br>KDV (%{t['kdv_oran']:g}): {kdv:,.2f} ₺<br>
<b>TOPLAM: {genel:,.2f} ₺</b></p></body></html>"""
        yol = os.path.join(tempfile.gettempdir(), f"teklif_{t['no'].replace('-', '_')}.html")
        with open(yol, "w", encoding="utf-8") as f:
            f.write(html)
        webbrowser.open("file://" + yol.replace("\\", "/"))

    # ---------- GÖREVLER ----------
    def gorev_kur(self):
        u = ttk.Frame(self.tg)
        u.pack(fill="x", pady=4)
        ttk.Button(u, text="+ Görev", command=self.gorev_form).pack(side="right", padx=3)
        ttk.Button(u, text="Durum", command=self.gorev_durum).pack(side="right", padx=3)
        ttk.Button(u, text="Sil", command=self.gorev_sil).pack(side="right", padx=3)
        self.t_gor = self.agac(self.tg, [("id", "ID", 40), ("b", "Görev", 240), ("m", "Müşteri", 170),
                                         ("s", "Bitiş", 100), ("d", "Durum", 90)])

    def gorev_form(self):
        mus = musteri_sozluk(self.db)
        w = tk.Toplevel(self)
        w.title("Görev")
        w.geometry("360x360")
        ttk.Label(w, text="Başlık *").pack(anchor="w", padx=12, pady=(8, 0))
        eb = ttk.Entry(w)
        eb.pack(padx=12, fill="x")
        ttk.Label(w, text="Müşteri (opsiyonel)").pack(anchor="w", padx=12, pady=(8, 0))
        cm = ttk.Combobox(w, values=[""] + list(mus.keys()))
        cm.pack(padx=12, fill="x")
        ttk.Label(w, text="Bitiş (YYYY-AA-GG)").pack(anchor="w", padx=12, pady=(8, 0))
        es = ttk.Entry(w)
        es.pack(padx=12, fill="x")
        es.insert(0, bugun())
        ttk.Label(w, text="Not").pack(anchor="w", padx=12, pady=(8, 0))
        en = ttk.Entry(w)
        en.pack(padx=12, fill="x")

        def k():
            if not eb.get().strip():
                messagebox.showwarning("Uyarı", "Başlık gerekli.", parent=w)
                return
            self.db.sorgu("INSERT INTO gorevler(baslik,musteri_id,bitis,notlar) VALUES(?,?,?,?)",
                          (eb.get().strip(), mus.get(cm.get()), es.get().strip(), en.get().strip()))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Kaydet", command=k).pack(pady=12)

    def secili_gorev(self):
        s = self.t_gor.selection()
        if not s:
            return None
        return self.db.listele("SELECT * FROM gorevler WHERE id=?",
                               (self.t_gor.item(s[0])["values"][0],))[0]

    def gorev_durum(self):
        g = self.secili_gorev()
        if not g:
            return
        w = tk.Toplevel(self)
        w.title("Görev Durumu")
        w.geometry("280x170")
        cb = ttk.Combobox(w, values=GOREV_DURUM, state="readonly")
        cb.pack(padx=12, pady=12, fill="x")
        cb.set(g["durum"])

        def uygula():
            self.db.sorgu("UPDATE gorevler SET durum=? WHERE id=?", (cb.get(), g["id"]))
            w.destroy()
            self.yenile()

        ttk.Button(w, text="Uygula", command=uygula).pack()

    def gorev_sil(self):
        g = self.secili_gorev()
        if g and messagebox.askyesno("Onay", "Görev silinsin mi?"):
            self.db.sorgu("DELETE FROM gorevler WHERE id=?", (g["id"],))
            self.yenile()

    # ---------- SMS & RAPOR ----------
    def sms_kur(self):
        u = ttk.Frame(self.tr)
        u.pack(fill="x", pady=4)
        ttk.Label(u, text="Toplu bilgilendirme SMS'i").pack(side="left")
        ttk.Button(u, text="✉️ SMS Gönderim Listesi", command=self.sms_liste).pack(side="right", padx=3)
        self.sms_txt = tk.Text(self.tr, height=7, font=("Segoe UI", 10))
        self.sms_txt.pack(fill="x", pady=4)
        bar = ttk.Frame(self.tr)
        bar.pack(fill="x", pady=2)
        ttk.Label(bar, text="📈 Rapor", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(bar, text="⬇ CSV: Fırsatlar", command=lambda: self.rapor_csv("f")).pack(side="right", padx=3)
        ttk.Button(bar, text="⬇ CSV: Müşteriler", command=lambda: self.rapor_csv("m")).pack(side="right", padx=3)
        self.rapor_txt = tk.Text(self.tr, height=9, font=("Consolas", 10), bg="#0d1426", fg="#a7f3d0")
        self.rapor_txt.pack(fill="both", expand=True)

    def sms_liste(self):
        rows = self.db.listele("SELECT id, firma, yetkili, telefon FROM musteriler WHERE telefon<>'' ORDER BY firma")
        self.sms_txt.delete("1.0", "end")
        if not rows:
            self.sms_txt.insert("1.0", "Telefonlu müşteri yok.")
            return
        sablon = ayar(self.db, "sms_sablon")
        for r in rows:
            ad = r["firma"] or r["yetkili"]
            try:
                m = sablon.format(ad=ad, isletme=ayar(self.db, "isletme"))
            except (KeyError, ValueError):
                m = f"Merhaba {ad}."
            self.db.sorgu("INSERT INTO sms_log(tarih,telefon,mesaj,durum) VALUES(?,?,?,?)",
                          (bugun(), r["telefon"], m, "Hazırlandı"))
            self.sms_txt.insert("end", f"📱 {r['telefon']} → {m}\n\n")
        self.clipboard_clear()
        self.clipboard_append(self.sms_txt.get("1.0", "end").strip())
        messagebox.showinfo("SMS", f"{len(rows)} mesaj hazır, kopyalandı.")

    def rapor_csv(self, tur):
        klasor = filedialog.askdirectory(title="CSV klasörü")
        if not klasor:
            return
        db = self.db
        if tur == "f":
            rows = db.listele("""SELECT f.id, m.firma, f.baslik, f.tutar, f.olasilik, f.asama
                FROM firsatlar f LEFT JOIN musteriler m ON m.id=f.musteri_id ORDER BY f.id DESC""")
            csv_yaz(klasor, "firsatlar.csv", ["ID", "Müşteri", "Fırsat", "Tutar", "%", "Aşama"],
                    [[r["id"], r["firma"], r["baslik"], r["tutar"], r["olasilik"], r["asama"]] for r in rows])
        else:
            rows = db.listele("SELECT id, firma, yetkili, telefon, eposta, kaynak FROM musteriler ORDER BY firma")
            csv_yaz(klasor, "musteriler.csv", ["ID", "Firma", "Yetkili", "Telefon", "E-posta", "Kaynak"],
                    [[r["id"], r["firma"], r["yetkili"], r["telefon"], r["eposta"], r["kaynak"]] for r in rows])
        messagebox.showinfo("CSV", f"Dışa aktarıldı:\n{klasor}")

    # ---------- YENİLE ----------
    def yenile(self):
        db = self.db
        ay = date.today().strftime("%Y-%m")
        acik = db.listele("SELECT COUNT(*) s FROM firsatlar WHERE asama NOT IN ('Kazanıldı','Kaybedildi')")[0]["s"]
        self.deger["frs"].config(text=str(acik))
        self.deger["agr"].config(text=tl(agirlikli_ciro(db)))
        tkp = db.listele("SELECT COUNT(*) s FROM aktiviteler WHERE takip<>'' AND takip<=?", (bugun(),))[0]["s"]
        tkp += db.listele("SELECT COUNT(*) s FROM gorevler WHERE durum!='Bitti' AND bitis<>'' AND bitis<=?",
                          (bugun(),))[0]["s"]
        self.deger["tkp"].config(text=str(tkp))

        for t in (self.t_sicak, self.t_takip, self.t_firsat, self.t_mus, self.t_akt, self.t_tek, self.t_gor):
            for i in t.get_children():
                t.delete(i)
        i = 0
        for r in db.listele("""SELECT f.baslik, m.firma, f.tutar FROM firsatlar f
            LEFT JOIN musteriler m ON m.id=f.musteri_id
            WHERE f.asama IN ('Teklif','Pazarlık') ORDER BY f.tutar DESC LIMIT 50"""):
            self.satir(self.t_sicak, i, (r["baslik"], r["firma"], tl(r["tutar"])))
            i += 1
        i = 0
        for r in db.listele("""SELECT a.tur, m.firma, a.ozet FROM aktiviteler a
            LEFT JOIN musteriler m ON m.id=a.musteri_id
            WHERE a.takip<>'' AND a.takip<=? ORDER BY a.takip LIMIT 50""", (bugun(),)):
            self.satir(self.t_takip, i, (r["tur"], r["firma"], r["ozet"]), "warn")
            i += 1
        i = 0
        for r in db.listele("""SELECT f.*, m.firma FROM firsatlar f
            LEFT JOIN musteriler m ON m.id=f.musteri_id ORDER BY f.id DESC LIMIT 300"""):
            tag = "ok" if r["asama"] == "Kazanıldı" else ("kritik" if r["asama"] == "Kaybedildi" else
                                                         ("even" if i % 2 else "odd"))
            self.satir(self.t_firsat, i, (r["id"], r["baslik"], r["firma"], tl(r["tutar"]),
                                          f"%{r['olasilik']}", r["asama"]), tag)
            i += 1
        q = (self.mq.get() or "").strip()
        rows = db.listele("SELECT * FROM musteriler WHERE firma LIKE ? OR yetkili LIKE ? OR telefon LIKE ? ORDER BY firma",
                          (f"%{q}%", f"%{q}%", f"%{q}%")) if q else \
            db.listele("SELECT * FROM musteriler ORDER BY firma LIMIT 400")
        for j, m in enumerate(rows):
            self.satir(self.t_mus, j, (m["id"], m["firma"], m["yetkili"], m["telefon"], m["kaynak"]))
        for j, r in enumerate(db.listele("""SELECT a.*, m.firma FROM aktiviteler a
            LEFT JOIN musteriler m ON m.id=a.musteri_id ORDER BY a.id DESC LIMIT 200""")):
            self.satir(self.t_akt, j, (r["id"], r["tarih"], r["tur"], r["firma"], r["ozet"], r["takip"] or "-"))
        for j, r in enumerate(db.listele("""SELECT t.*, m.firma FROM teklifler t
            LEFT JOIN musteriler m ON m.id=t.musteri_id ORDER BY t.id DESC LIMIT 200""")):
            _, _, genel = teklif_toplam(db, r["id"])
            self.satir(self.t_tek, j, (r["id"], r["no"], r["firma"], tl(genel), r["durum"]),
                       "ok" if r["durum"] == "Onaylandı" else ("kritik" if r["durum"] == "Reddedildi" else ""))
        for j, r in enumerate(db.listele("""SELECT g.*, m.firma FROM gorevler g
            LEFT JOIN musteriler m ON m.id=g.musteri_id ORDER BY g.id DESC LIMIT 200""")):
            v = vade_yakin_mi(r["bitis"]) if r["durum"] != "Bitti" else ""
            self.satir(self.t_gor, j, (r["id"], r["baslik"], r["firma"] or "-", r["bitis"], r["durum"]),
                       "kritik" if v == "gecmis" else ("warn" if v == "yakin" else ""))
        kazan = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM firsatlar WHERE asama='Kazanıldı'")[0]["s"] or 0
        sat = [f"===== {ay} SATIŞ RAPORU =====", f"Açık fırsat: {acik}",
               f"Ağırlıklı ciro: {tl(agirlikli_ciro(db))}", f"Kazanılan (toplam): {tl(kazan)}", "",
               "--- Aşama Dağılımı ---"]
        for r in db.listele("SELECT asama, COUNT(*) n, COALESCE(SUM(tutar),0) t FROM firsatlar GROUP BY asama"):
            sat.append(f"{r['asama']}: {r['n']} fırsat, {tl(r['t'])}")
        sat.append("")
        sat.append("--- Kaynak Dağılımı ---")
        for r in db.listele("SELECT kaynak, COUNT(*) n FROM musteriler GROUP BY kaynak"):
            sat.append(f"{r['kaynak'] or '?'}: {r['n']} müşteri")
        self.rapor_txt.delete("1.0", "end")
        self.rapor_txt.insert("1.0", "\n".join(sat))


def main():
    db = Veritabani()
    if durum(db)["kilitli"] and not kilit_goster(db):
        return
    App(db).mainloop()
