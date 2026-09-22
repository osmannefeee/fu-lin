# -*- coding: utf-8 -*-
"""📅 Randevular + ✉️ SMS hatırlatma."""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from .sabitler import RANDEVU_DURUM, SAAT_FMT, TARIH_FMT, TEDAVI_FIYAT
from .tema import cift_tag, tablo_kur
from .yardim import ayar_get, ayar_set, bugun_str, hekim_sec_dict, hasta_sec_dict, netgsm_gonder, sms_metni_uret, yarin_str


class SekmeRandevu(ttk.Frame):
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        self.app = app
        ust = ttk.Frame(self)
        ust.pack(fill="x", pady=4)
        ttk.Label(ust, text="Tarih (YYYY-AA-GG, boş=tümü):").pack(side="left")
        self.tarih = ttk.Entry(ust, width=14)
        self.tarih.pack(side="left", padx=4)
        self.tarih.insert(0, bugun_str())
        ttk.Button(ust, text="Filtrele", command=self.yenile).pack(side="left", padx=4)
        ttk.Button(ust, text="Tümü", command=self.tumu).pack(side="left")
        ttk.Button(ust, text="✉️ SMS Hatırlatma", command=self.sms_penceresi).pack(side="right", padx=4)
        ttk.Button(ust, text="Sil", command=self.sil).pack(side="right", padx=4)
        ttk.Button(ust, text="Durum Değiştir", command=self.durum_form).pack(side="right", padx=4)
        ttk.Button(ust, text="+ Yeni Randevu", command=self.form).pack(side="right", padx=4)
        self.tree = tablo_kur(self, [("id", "ID", 45), ("tarih", "Tarih", 100), ("saat", "Saat", 70),
                                     ("hasta", "Hasta", 190), ("hekim", "Hekim", 170),
                                     ("islem", "İşlem", 170), ("durum", "Durum", 100)])

    def tumu(self):
        self.tarih.delete(0, "end")
        self.yenile()

    def yenile(self):
        db = self.app.db
        t = self.tarih.get().strip()
        for i in self.tree.get_children():
            self.tree.delete(i)
        sql = """SELECT r.*, h.ad_soyad hasta, hk.ad_soyad hekim FROM randevular r
                 LEFT JOIN hastalar h ON h.id=r.hasta_id LEFT JOIN hekimler hk ON hk.id=r.hekim_id"""
        rows = db.listele(sql + " WHERE r.tarih=? ORDER BY r.saat", (t,)) if t else \
            db.listele(sql + " ORDER BY r.tarih DESC, r.saat DESC LIMIT 500")
        for i, r in enumerate(rows):
            tag = ("ok",) if r["durum"] == "Geldi" else \
                ("kritik",) if r["durum"] in ("Gelmedi", "İptal") else cift_tag(i)
            self.tree.insert("", "end", values=(r["id"], r["tarih"], r["saat"], r["hasta"],
                                                r["hekim"], r["islem"], r["durum"]), tags=tag)

    def secili_id(self):
        s = self.tree.selection()
        return self.tree.item(s[0])["values"][0] if s else None

    def form(self):
        db = self.app.db
        hastalar = hasta_sec_dict(db)
        hekimler = hekim_sec_dict(db)
        if not hastalar:
            messagebox.showinfo("Bilgi", "Önce hasta ekleyin.")
            return
        win = tk.Toplevel(self)
        win.title("Randevu")
        win.geometry("420x460")
        ttk.Label(win, text="Hasta").pack(anchor="w", padx=12, pady=(8, 0))
        cb_h = ttk.Combobox(win, values=list(hastalar.keys()), width=50)
        cb_h.pack(padx=12, fill="x")
        ttk.Label(win, text="Hekim").pack(anchor="w", padx=12, pady=(8, 0))
        cb_he = ttk.Combobox(win, values=list(hekimler.keys()), width=50)
        cb_he.pack(padx=12, fill="x")
        if hekimler:
            cb_he.set(list(hekimler.keys())[0])
        ttk.Label(win, text="Tarih (YYYY-AA-GG)").pack(anchor="w", padx=12, pady=(8, 0))
        e_t = ttk.Entry(win)
        e_t.pack(padx=12, fill="x")
        e_t.insert(0, bugun_str())
        ttk.Label(win, text="Saat (HH:MM)").pack(anchor="w", padx=12, pady=(8, 0))
        e_s = ttk.Entry(win)
        e_s.pack(padx=12, fill="x")
        e_s.insert(0, "10:00")
        ttk.Label(win, text="İşlem").pack(anchor="w", padx=12, pady=(8, 0))
        cb_i = ttk.Combobox(win, values=list(TEDAVI_FIYAT.keys()), width=50)
        cb_i.pack(padx=12, fill="x")
        cb_i.set("Muayene")
        ttk.Label(win, text="Not").pack(anchor="w", padx=12, pady=(8, 0))
        e_n = ttk.Entry(win)
        e_n.pack(padx=12, fill="x")

        def kaydet():
            if cb_h.get() not in hastalar:
                messagebox.showwarning("Uyarı", "Hasta seçin.", parent=win)
                return
            try:
                datetime.strptime(e_t.get().strip(), TARIH_FMT)
                datetime.strptime(e_s.get().strip(), SAAT_FMT)
            except ValueError:
                messagebox.showwarning("Uyarı", "Tarih/Saat formatı hatalı.", parent=win)
                return
            heid = hekimler.get(cb_he.get())
            if heid:
                c = db.listele("""SELECT COUNT(*) s FROM randevular WHERE hekim_id=? AND tarih=?
                                  AND saat=? AND durum='Planlandı'""",
                               (heid, e_t.get().strip(), e_s.get().strip()))[0]["s"]
                if c and not messagebox.askyesno("Çakışma", "Bu hekimin bu saatte randevusu var. Yine de ekle?",
                                                 parent=win):
                    return
            db.sorgu("INSERT INTO randevular(hasta_id, hekim_id, tarih, saat, islem, notlar) VALUES(?,?,?,?,?,?)",
                     (hastalar[cb_h.get()], heid, e_t.get().strip(), e_s.get().strip(),
                      cb_i.get(), e_n.get().strip()))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=12)

    def durum_form(self):
        rid = self.secili_id()
        if not rid:
            return
        win = tk.Toplevel(self)
        win.title("Durum Değiştir")
        win.geometry("280x180")
        ttk.Label(win, text="Yeni durum:").pack(pady=8)
        cb = ttk.Combobox(win, values=RANDEVU_DURUM)
        cb.pack(padx=12, fill="x")
        cb.set("Geldi")

        def uygula():
            self.app.db.sorgu("UPDATE randevular SET durum=? WHERE id=?", (cb.get(), rid))
            win.destroy()
            self.app.yenile_hepsi()

        ttk.Button(win, text="Uygula", command=uygula).pack(pady=10)

    def sil(self):
        rid = self.secili_id()
        if rid and messagebox.askyesno("Onay", "Randevu silinsin mi?"):
            self.app.db.sorgu("DELETE FROM randevular WHERE id=?", (rid,))
            self.app.yenile_hepsi()

    # ---------- SMS ----------
    def sms_penceresi(self):
        db = self.app.db
        win = tk.Toplevel(self)
        win.title("✉️ SMS Hatırlatma")
        win.geometry("760x600")
        ust = ttk.Frame(win, padding=8)
        ust.pack(fill="x")
        ttk.Label(ust, text="Tarih:").pack(side="left")
        e_t = ttk.Entry(ust, width=12)
        e_t.pack(side="left", padx=4)
        e_t.insert(0, yarin_str())
        ttk.Button(ust, text="Listele", command=lambda: listele()).pack(side="left", padx=4)
        ttk.Button(ust, text="⚙️ SMS Ayarları", command=lambda: self.sms_ayarlari(win)).pack(side="right", padx=4)
        tree = tablo_kur(win, [("hasta", "Hasta", 200), ("tel", "Telefon", 130),
                               ("saat", "Saat", 70), ("hekim", "Hekim", 170)])
        ttk.Label(win, text="Mesaj önizleme:").pack(anchor="w", padx=8, pady=(8, 0))
        txt = tk.Text(win, height=10, font=("Segoe UI", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=4)
        veriler = []

        def listele():
            nonlocal veriler
            for i in tree.get_children():
                tree.delete(i)
            txt.delete("1.0", "end")
            veriler = db.listele("""SELECT r.*, h.ad_soyad hasta, h.telefon, hk.ad_soyad hekim
                FROM randevular r LEFT JOIN hastalar h ON h.id=r.hasta_id
                LEFT JOIN hekimler hk ON hk.id=r.hekim_id
                WHERE r.tarih=? AND r.durum='Planlandı' ORDER BY r.saat""", (e_t.get().strip(),))
            if not veriler:
                txt.insert("1.0", "Bu tarihte hatırlatma gönderilecek randevu yok.")
                return
            for i, r in enumerate(veriler):
                tree.insert("", "end", values=(r["hasta"], r["telefon"], r["saat"], r["hekim"]),
                            tags=cift_tag(i))
                txt.insert("end", f"📱 {r['telefon']} → "
                           f"{sms_metni_uret(db, r['hasta'], r['tarih'], r['saat'], r['hekim'] or '')}\n\n")

        def kopyala():
            self.clipboard_clear()
            self.clipboard_append(txt.get("1.0", "end").strip())
            messagebox.showinfo("Kopyalandı", "Mesajlar panoya kopyalandı.", parent=win)

        def logla(durum):
            for r in veriler:
                m = sms_metni_uret(db, r["hasta"], r["tarih"], r["saat"], r["hekim"] or "")
                db.sorgu("INSERT INTO sms_log(tarih, hasta_id, telefon, mesaj, durum) VALUES(?,?,?,?,?)",
                         (bugun_str(), r["hasta_id"], r["telefon"], m, durum))
            messagebox.showinfo("SMS", f"{len(veriler)} mesaj loga kaydedildi ({durum}).", parent=win)

        def gonder():
            if not veriler:
                messagebox.showinfo("SMS", "Önce listeleyin.", parent=win)
                return
            if not messagebox.askyesno("Onay", f"{len(veriler)} SMS gönderilsin mi?", parent=win):
                return
            ok = 0
            for r in veriler:
                m = sms_metni_uret(db, r["hasta"], r["tarih"], r["saat"], r["hekim"] or "")
                basari, bilgi = netgsm_gonder(db, r["telefon"], m)
                db.sorgu("INSERT INTO sms_log(tarih, hasta_id, telefon, mesaj, durum) VALUES(?,?,?,?,?)",
                         (bugun_str(), r["hasta_id"], r["telefon"], m,
                          "Gönderildi" if basari else f"Simülasyon/Hata: {bilgi}"))
                ok += 1 if basari else 0
            messagebox.showinfo("SMS", f"Başarılı: {ok}/{len(veriler)}", parent=win)

        bar = ttk.Frame(win, padding=8)
        bar.pack(fill="x")
        ttk.Button(bar, text="📋 Tümünü Kopyala", command=kopyala).pack(side="left", padx=4)
        ttk.Button(bar, text="💾 Loga Kaydet", command=lambda: logla("Hazırlandı")).pack(side="left", padx=4)
        ttk.Button(bar, text="🚀 NetGSM ile Gönder", command=gonder).pack(side="right", padx=4)
        ttk.Button(bar, text="📜 SMS Logu", command=self.sms_log_goster).pack(side="right", padx=4)
        listele()

    def sms_ayarlari(self, parent):
        db = self.app.db
        win = tk.Toplevel(parent)
        win.title("SMS Ayarları")
        win.geometry("460x380")
        alanlar = {}
        for etiket, anahtar in [("Klinik adı", "klinik_adi"), ("SMS şablonu", "sms_sablon"),
                                ("NetGSM kullanıcı", "netgsm_user"), ("NetGSM şifre", "netgsm_pass"),
                                ("NetGSM başlık", "netgsm_header")]:
            ttk.Label(win, text=etiket).pack(anchor="w", padx=12, pady=(6, 0))
            e = ttk.Entry(win, width=55)
            e.pack(padx=12, fill="x")
            e.insert(0, ayar_get(db, anahtar))
            alanlar[anahtar] = e
        ttk.Label(win, text="Değişkenler: {hasta} {tarih} {saat} {hekim} {klinik}",
                  font=("Segoe UI", 8)).pack(padx=12, pady=6)

        def kaydet():
            for k, e in alanlar.items():
                ayar_set(db, k, e.get())
            messagebox.showinfo("Ayarlar", "Kaydedildi.", parent=win)
            win.destroy()

        ttk.Button(win, text="Kaydet", command=kaydet).pack(pady=10)

    def sms_log_goster(self):
        win = tk.Toplevel(self)
        win.title("SMS Logu")
        win.geometry("700x420")
        tree = tablo_kur(win, [("tarih", "Tarih", 90), ("tel", "Telefon", 120),
                               ("mesaj", "Mesaj", 320), ("durum", "Durum", 150)])
        for i, r in enumerate(self.app.db.listele("SELECT * FROM sms_log ORDER BY id DESC LIMIT 300")):
            tree.insert("", "end", values=(r["tarih"], r["telefon"], (r["mesaj"] or "")[:80], r["durum"]),
                        tags=cift_tag(i))
