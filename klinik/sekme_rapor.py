# -*- coding: utf-8 -*-
"""📈 Raporlar + 👥 kullanıcı yönetimi + 💾 yedek."""
import csv
import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from .sabitler import ROLLER
from .yardim import para_fmt, sifre_hashla


class SekmeRapor(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        ust = ttk.Frame(self)
        ust.pack(fill="x", pady=4)
        ttk.Label(ust, text="Ay (YYYY-AA):").pack(side="left")
        self.ay = ttk.Entry(ust, width=10)
        self.ay.pack(side="left", padx=4)
        self.ay.insert(0, date.today().strftime("%Y-%m"))
        ttk.Button(ust, text="📈 Hesapla", command=self.yenile).pack(side="left", padx=4)
        self.metin = tk.Text(self, height=25, font=("Consolas", 10),
                             bg="#0f172a", fg="#e2e8f0", insertbackground="white")
        self.metin.pack(fill="both", expand=True, pady=6)

    def yenile(self):
        db = self.app.db
        ay = self.ay.get().strip() or date.today().strftime("%Y-%m")
        tahsilat = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler WHERE substr(tarih,1,7)=?",
                              (ay,))[0]["s"] or 0
        gider = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM giderler WHERE substr(tarih,1,7)=?",
                           (ay,))[0]["s"] or 0
        kesilen = db.listele("SELECT COALESCE(SUM(toplam_ucret),0) s FROM tedaviler WHERE substr(tarih,1,7)=?",
                             (ay,))[0]["s"] or 0
        top_ted = db.listele("SELECT COALESCE(SUM(toplam_ucret),0) s FROM tedaviler")[0]["s"] or 0
        top_ode = db.listele("SELECT COALESCE(SUM(tutar),0) s FROM odemeler")[0]["s"] or 0
        n_ran = db.listele("SELECT COUNT(*) s FROM randevular WHERE substr(tarih,1,7)=?", (ay,))[0]["s"]
        hek = db.listele("""SELECT hk.ad_soyad h, COALESCE(SUM(t.toplam_ucret),0) c, COUNT(*) n
            FROM tedaviler t LEFT JOIN hekimler hk ON hk.id=t.hekim_id
            WHERE substr(t.tarih,1,7)=? GROUP BY hk.ad_soyad ORDER BY c DESC""", (ay,))
        islem = db.listele("""SELECT islem, COUNT(*) n, COALESCE(SUM(toplam_ucret),0) c
            FROM tedaviler WHERE substr(tarih,1,7)=? GROUP BY islem ORDER BY c DESC""", (ay,))
        satir = [f"===== {ay} AYI KLİNİK RAPORU =====",
                 f"Kesilen tedavi tutarı : {para_fmt(kesilen)}",
                 f"Tahsilat              : {para_fmt(tahsilat)}",
                 f"Gider                 : {para_fmt(gider)}",
                 f"Net (tahsilat-gider)  : {para_fmt(tahsilat - gider)}",
                 f"Randevu sayısı        : {n_ran}",
                 f"Genel alacak (kalan)  : {para_fmt(top_ted - top_ode)}",
                 "", "--- Hekim Bazında Kesilen ---"]
        satir += [f"{r['h'] or 'Atanmamış'}: {r['n']} işlem, {para_fmt(r['c'])}" for r in hek]
        satir += ["", "--- İşlem Bazında ---"]
        satir += [f"{r['islem']}: {r['n']} adet, {para_fmt(r['c'])}" for r in islem]
        self.metin.delete("1.0", "end")
        self.metin.insert("1.0", "\n".join(satir))


def kullanici_yonetimi(pencere, db):
    import sqlite3
    win = tk.Toplevel(pencere)
    win.title("Kullanıcı Yönetimi")
    win.geometry("620x400")
    tree = ttk.Treeview(win, columns=("id", "kadi", "ad", "rol", "durum"), show="headings")
    for k, b, w in [("id", "ID", 45), ("kadi", "Kullanıcı Adı", 140), ("ad", "Ad Soyad", 180),
                    ("rol", "Rol", 100), ("durum", "Durum", 80)]:
        tree.heading(k, text=b)
        tree.column(k, width=w)
    tree.pack(fill="both", expand=True, padx=10, pady=8)

    def listele():
        for i in tree.get_children():
            tree.delete(i)
        for r in db.listele("SELECT * FROM kullanicilar ORDER BY kullanici_adi"):
            tree.insert("", "end", values=(r["id"], r["kullanici_adi"], r["ad_soyad"], r["rol"],
                                           "Aktif" if r["aktif"] else "Pasif"))

    def form(kayit=None):
        f = tk.Toplevel(win)
        f.title("Kullanıcı")
        f.geometry("360x340")
        ttk.Label(f, text="Kullanıcı adı *").pack(anchor="w", padx=12, pady=(8, 0))
        e_k = ttk.Entry(f)
        e_k.pack(padx=12, fill="x")
        ttk.Label(f, text="Ad Soyad").pack(anchor="w", padx=12, pady=(8, 0))
        e_a = ttk.Entry(f)
        e_a.pack(padx=12, fill="x")
        ttk.Label(f, text="Rol").pack(anchor="w", padx=12, pady=(8, 0))
        cb = ttk.Combobox(f, values=ROLLER)
        cb.pack(padx=12, fill="x")
        cb.set("sekreter")
        ttk.Label(f, text="Şifre (boş=bırak)").pack(anchor="w", padx=12, pady=(8, 0))
        e_s = ttk.Entry(f, show="•")
        e_s.pack(padx=12, fill="x")
        if kayit:
            e_k.insert(0, kayit["kullanici_adi"])
            e_k.config(state="disabled")
            e_a.insert(0, kayit["ad_soyad"] or "")
            cb.set(kayit["rol"])

        def kaydet():
            ka = (kayit["kullanici_adi"] if kayit else e_k.get().strip())
            if not ka:
                messagebox.showwarning("Uyarı", "Kullanıcı adı zorunlu.", parent=f)
                return
            if kayit:
                if e_s.get():
                    db.sorgu("UPDATE kullanicilar SET ad_soyad=?, rol=?, sifre_hash=? WHERE id=?",
                             (e_a.get().strip(), cb.get(), sifre_hashla(e_s.get()), kayit["id"]))
                else:
                    db.sorgu("UPDATE kullanicilar SET ad_soyad=?, rol=? WHERE id=?",
                             (e_a.get().strip(), cb.get(), kayit["id"]))
            else:
                if not e_s.get():
                    messagebox.showwarning("Uyarı", "Şifre zorunlu.", parent=f)
                    return
                try:
                    db.sorgu("INSERT INTO kullanicilar(kullanici_adi, sifre_hash, rol, ad_soyad) VALUES(?,?,?,?)",
                             (ka, sifre_hashla(e_s.get()), cb.get(), e_a.get().strip()))
                except sqlite3.IntegrityError:
                    messagebox.showwarning("Uyarı", "Bu kullanıcı adı zaten var.", parent=f)
                    return
            f.destroy()
            listele()

        ttk.Button(f, text="Kaydet", command=kaydet).pack(pady=12)

    def secili():
        s = tree.selection()
        if not s:
            return None
        hid = tree.item(s[0])["values"][0]
        return db.listele("SELECT * FROM kullanicilar WHERE id=?", (hid,))[0]

    def duzenle():
        k = secili()
        if k:
            form(k)

    def degistir():
        k = secili()
        if not k:
            return
        if k["kullanici_adi"] == "admin":
            messagebox.showwarning("Uyarı", "admin kapatılamaz.", parent=win)
            return
        db.sorgu("UPDATE kullanicilar SET aktif=? WHERE id=?", (0 if k["aktif"] else 1, k["id"]))
        listele()

    bar = ttk.Frame(win)
    bar.pack(fill="x", padx=10, pady=4)
    ttk.Button(bar, text="+ Yeni", command=lambda: form()).pack(side="right", padx=4)
    ttk.Button(bar, text="Düzenle", command=duzenle).pack(side="right", padx=4)
    ttk.Button(bar, text="Aktif/Pasif", command=degistir).pack(side="right", padx=4)
    listele()


def csv_yedek(pencere, db, sessiz=False):
    klasor = filedialog.askdirectory(title="Yedek klasörü seçin", parent=pencere)
    if not klasor:
        return 0
    n = 0
    for tablo in ["hastalar", "hekimler", "randevular", "tedaviler", "odemeler", "stok",
                  "giderler", "kullanicilar", "dis_durum", "sms_log", "ayarlar"]:
        rows = db.listele(f"SELECT * FROM {tablo}")
        with open(os.path.join(klasor, f"{tablo}.csv"), "w", newline="", encoding="utf-8-sig") as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                for r in rows:
                    w.writerow(dict(r))
                n += len(rows)
    if not sessiz:
        messagebox.showinfo("Yedek", f"{n} kayıt yedeklendi:\n{klasor}", parent=pencere)
    return n
