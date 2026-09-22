# -*- coding: utf-8 -*-
"""Ana pencere: üst bar, sekmeler, geçişler, hata tuzağı."""
import os
import tkinter as tk
import traceback
from datetime import datetime
from tkinter import messagebox, ttk

from . import SURUM
from .giris import giris_yap
from .lisans import kilit_penceresi, lisans_aktivasyon_formu, lisans_durumu
from .sabitler import LISANS_TEL
from .sekme_hasta import SekmeHasta
from .sekme_hekim import SekmeHekim
from .sekme_panel import SekmePanel
from .sekme_randevu import SekmeRandevu
from .sekme_rapor import SekmeRapor, csv_yedek, kullanici_yonetimi
from .sekme_sema import SekmeSema
from .sekme_stok import SekmeStok
from .sekme_tedavi import SekmeTedavi
from .tema import tema_uygula
from .veritabani import DB_ADI, Veritabani
from .yardim import ayar_get, bugun_str


class KlinikApp(tk.Tk):
    def __init__(self, db, kullanici):
        super().__init__()
        self.db = db
        self.kullanici = kullanici
        self.secili_hasta = None
        self.report_callback_exception = self._hata_rapor
        self.title(f"Özel Diş Kliniği — Yönetim Takip Sistemi v{SURUM}")
        self.geometry("1300x780")
        self.minsize(1150, 680)
        self.configure(bg="#f1f5f9")
        tema_uygula(self)

        ust = tk.Frame(self, bg="#0f172a")
        ust.pack(fill="x")
        tk.Label(ust, text="  🦷  Diş Sağlığı Merkezi", font=("Segoe UI", 14, "bold"),
                 bg="#0f172a", fg="white").pack(side="left", pady=10)
        tk.Label(ust, text=f"   📅 {bugun_str()}  •  v{SURUM}", font=("Segoe UI", 10),
                 bg="#0f172a", fg="#94a3b8").pack(side="left")
        tk.Label(ust, text=f"👤 {kullanici.get('ad_soyad')} ({kullanici.get('rol')})  ",
                 font=("Segoe UI", 10, "bold"), bg="#0f172a", fg="#5eead4").pack(side="right", padx=4)
        self.lisans = lisans_durumu(db)
        if self.lisans["tip"] == "deneme":
            tk.Label(ust, text=f"  ⏳ Deneme: {self.lisans['kalan']} gün  ",
                     font=("Segoe UI", 10, "bold"), bg="#7c2d12", fg="#fed7aa").pack(side="right", padx=4)
        ttk.Button(ust, text="⏻ Çıkış", command=self.cikis).pack(side="right", padx=8, pady=10)
        ttk.Button(ust, text="🔑 Lisans", command=self.lisans_penc).pack(side="right", padx=3, pady=10)
        if kullanici.get("rol") == "admin":
            ttk.Button(ust, text="👥 Kullanıcılar", command=self.kullanici_ac).pack(side="right", padx=3, pady=10)
        ttk.Button(ust, text="💾 Yedek", command=self.yedek_al).pack(side="right", padx=3, pady=10)
        ttk.Button(ust, text="Yenile", command=self.yenile_hepsi).pack(side="right", padx=3, pady=10)
        self.protocol("WM_DELETE_WINDOW", self.cikis)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=8)
        self.sekme_panel = SekmePanel(self)
        self.sekme_hasta = SekmeHasta(self)
        self.sekme_randevu = SekmeRandevu(self)
        self.sekme_sema = SekmeSema(self)
        self.sekme_tedavi = SekmeTedavi(self)
        self.sekme_hekim = SekmeHekim(self)
        self.sekme_stok = SekmeStok(self)
        self.sekme_rapor = SekmeRapor(self)
        for sekme, baslik in [
                (self.sekme_panel, "📊 Panel"), (self.sekme_hasta, "👥 Hastalar"),
                (self.sekme_randevu, "📅 Randevular"), (self.sekme_sema, "🦷 Diş Şeması"),
                (self.sekme_tedavi, "💳 Tedavi & Ödeme"), (self.sekme_hekim, "🩺 Hekimler"),
                (self.sekme_stok, "📦 Stok & Gider"), (self.sekme_rapor, "📈 Raporlar")]:
            self.notebook.add(sekme, text=f"  {baslik}  ")
        self.sekmeler = [self.sekme_panel, self.sekme_hasta, self.sekme_randevu, self.sekme_sema,
                         self.sekme_tedavi, self.sekme_hekim, self.sekme_stok, self.sekme_rapor]
        self.yenile_hepsi()

    # ---------- genel ----------
    def _hata_rapor(self, exc, val, tb):
        try:
            with open(os.path.join(os.path.dirname(DB_ADI), "hata.log"), "a", encoding="utf-8") as f:
                f.write(f"\n===== {datetime.now()} =====\n")
                traceback.print_exception(exc, val, tb, file=f)
        except Exception:
            pass
        try:
            messagebox.showerror("Hata", f"İşlem yapılamadı:\n{val}\n\nDetay: hata.log")
        except Exception:
            pass

    def cikis(self):
        try:
            self.destroy()
        finally:
            os._exit(0)

    def yenile_hepsi(self):
        for s in self.sekmeler:
            try:
                s.yenile()
            except Exception as e:
                messagebox.showwarning("Uyarı", f"Bir sekme yenilenemedi:\n{e}")

    # ---------- geçişler ----------
    def tedavi_ac(self, hasta_id, dis_no=""):
        self.secili_hasta = hasta_id
        self.sekme_tedavi.hasta_sec(hasta_id)
        self.notebook.select(self.sekme_tedavi)
        if dis_no:
            self.sekme_tedavi.tedavi_ekle(dis_no)

    def sema_ac(self, hasta_id):
        self.secili_hasta = hasta_id
        self.sekme_sema.hasta_sec(hasta_id)
        self.notebook.select(self.sekme_sema)

    # ---------- üst bar ----------
    def lisans_penc(self):
        win = tk.Toplevel(self)
        win.title("Lisans")
        win.geometry("380x380")
        d = lisans_durumu(self.db)
        if d["tip"] == "tam":
            ttk.Label(win, text="✅ Tam lisans aktif", font=("Segoe UI", 12, "bold")).pack(pady=12)
            ttk.Label(win, text=f"Müşteri: {ayar_get(self.db, 'lisans_musteri')}").pack()
        else:
            ttk.Label(win, text=f"⏳ Deneme: {d['kalan']} gün kaldı",
                      font=("Segoe UI", 12, "bold")).pack(pady=12)
            ttk.Label(win, text=f"Satın alma: {LISANS_TEL}").pack()
            lisans_aktivasyon_formu(win, self.db)

    def kullanici_ac(self):
        if self.kullanici.get("rol") != "admin":
            messagebox.showwarning("Yetki", "Sadece admin.")
            return
        kullanici_yonetimi(self, self.db)

    def yedek_al(self):
        csv_yedek(self, self.db)


def main():
    try:
        db = Veritabani()
    except Exception as e:
        tk.Tk().withdraw()
        messagebox.showerror("Veritabanı", f"Veritabanı açılamadı:\n{e}")
        return
    durum = lisans_durumu(db)
    if durum["kilitli"] and not kilit_penceresi(db, durum):
        return
    user = giris_yap(db)
    if not user:
        return
    KlinikApp(db, user).mainloop()
