# Fu-Lin site sunucusu + admin paneli (tek dosya, ek kurulum yok)
# Calistirma: python server.py  ->  site: http://localhost:8000  admin: http://localhost:8000/admin
# NOT: ADMIN_SIFRE'yi ilk iş olarak değiştir.
import json
import os
import sqlite3
import hashlib
import secrets
import urllib.parse
from datetime import datetime, date, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BURADA = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BURADA, "fulin.db")
ADMIN_SIFRE = "efe333"
OTURUMLAR = {}  # token -> son kullanim

MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8", ".jpg": "image/jpeg",
        ".png": "image/png", ".ico": "image/x-icon", ".exe": "application/octet-stream"}


def baglan():
    b = sqlite3.connect(DB)
    b.row_factory = sqlite3.Row
    return b


def kur():
    b = baglan()
    c = b.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS talepler(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, ad TEXT, tel TEXT,
        urun TEXT, notlar TEXT, durum TEXT DEFAULT 'yeni', kaynak TEXT DEFAULT 'site')""")
    c.execute("""CREATE TABLE IF NOT EXISTS ziyaretler(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, sayfa TEXT, ip TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS indirmeler(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, dosya TEXT, ip TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS siparisler(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, musteri TEXT, telefon TEXT,
        urun TEXT, tutar REAL DEFAULT 0, durum TEXT DEFAULT 'bekliyor', notlar TEXT)""")
    b.commit()
    b.close()


def simdi():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def jeton_uret():
    t = secrets.token_hex(24)
    OTURUMLAR[t] = datetime.now()
    return t


def jeton_ok(t):
    if not t or t not in OTURUMLAR:
        return False
    if datetime.now() - OTURUMLAR[t] > timedelta(hours=12):
        del OTURUMLAR[t]
        return False
    OTURUMLAR[t] = datetime.now()
    return True


class El(BaseHTTPRequestHandler):
    server_version = "FuLin/1.0"

    def log_message(self, *a):
        pass

    def _json(self, veri, kod=200):
        g = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(g)))
        self.end_headers()
        self.wfile.write(g)

    def _oku(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        ham = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(ham.decode("utf-8") or "{}")
        except ValueError:
            return {}

    def _ip(self):
        return (self.client_address[0] if self.client_address else "?")

    def _yetki(self):
        return jeton_ok((self.headers.get("Authorization") or "").replace("Bearer ", "").strip())

    # ---------- GET ----------
    def do_GET(self):
        yol = urllib.parse.urlparse(self.path).path
        if yol == "/admin":
            yol = "/admin.html"
        if yol.startswith("/api/admin/"):
            return self._admin_get(yol)
        if yol in ("/", ""):
            yol = "/index.html"
        # indirme sayacı: /indir/... isteklerini logla
        if yol.startswith("/indir/"):
            b = baglan()
            b.execute("INSERT INTO indirmeler(tarih, dosya, ip) VALUES(?,?,?)",
                      (simdi(), os.path.basename(yol), self._ip()))
            b.commit()
            b.close()
        dosya = os.path.normpath(os.path.join(BURADA, yol.lstrip("/")))
        if not dosya.startswith(BURADA) or not os.path.isfile(dosya):
            return self._json({"hata": "yok"}, 404)
        ext = os.path.splitext(dosya)[1].lower()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        if ext == ".exe":
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(dosya)}"')
        self.send_header("Content-Length", str(os.path.getsize(dosya)))
        self.end_headers()
        with open(dosya, "rb") as f:
            while True:
                p = f.read(65536)
                if not p:
                    break
                self.wfile.write(p)

    def _admin_get(self, yol):
        if not self._yetki():
            return self._json({"hata": "yetki"}, 401)
        b = baglan()
        if yol == "/api/admin/ozet":
            bugun = date.today().strftime("%Y-%m-%d")
            v = b.execute("SELECT COUNT(*) s FROM ziyaretler").fetchone()["s"]
            vb = b.execute("SELECT COUNT(*) s FROM ziyaretler WHERE substr(tarih,1,10)=?", (bugun,)).fetchone()["s"]
            t = b.execute("SELECT COUNT(*) s FROM talepler").fetchone()["s"]
            ty = b.execute("SELECT COUNT(*) s FROM talepler WHERE durum='yeni'").fetchone()["s"]
            d = b.execute("SELECT COUNT(*) s FROM indirmeler").fetchone()["s"]
            s = b.execute("SELECT COUNT(*) s FROM siparisler").fetchone()["s"]
            ciro = b.execute("SELECT COALESCE(SUM(tutar),0) c FROM siparisler WHERE durum='odendi'").fetchone()["c"] or 0
            gunler = []
            for i in range(6, -1, -1):
                g = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
                n = b.execute("SELECT COUNT(*) s FROM ziyaretler WHERE substr(tarih,1,10)=?", (g,)).fetchone()["s"]
                gunler.append({"gun": g[5:], "ziyaret": n})
            durumlar = [dict(r) for r in b.execute("SELECT durum, COUNT(*) n FROM talepler GROUP BY durum")]
            b.close()
            return self._json({"ziyaret": v, "bugun": vb, "talep": t, "yeni": ty,
                               "indirme": d, "siparis": s, "ciro": ciro,
                               "gunler": gunler, "durumlar": durumlar})
        if yol == "/api/admin/talepler":
            rows = [dict(r) for r in b.execute("SELECT * FROM talepler ORDER BY id DESC LIMIT 500")]
            b.close()
            return self._json(rows)
        if yol == "/api/admin/siparisler":
            rows = [dict(r) for r in b.execute("SELECT * FROM siparisler ORDER BY id DESC LIMIT 500")]
            b.close()
            return self._json(rows)
        if yol == "/api/admin/csv":
            q = urllib.parse.urlparse(self.path).query
            tablo = urllib.parse.parse_qs(q).get("tablo", ["talepler"])[0]
            if tablo not in ("talepler", "siparisler", "ziyaretler", "indirmeler"):
                tablo = "talepler"
            rows = b.execute(f"SELECT * FROM {tablo} ORDER BY id DESC").fetchall()
            b.close()
            import csv
            import io
            s = io.StringIO()
            if rows:
                w = csv.DictWriter(s, fieldnames=rows[0].keys())
                w.writeheader()
                for r in rows:
                    w.writerow(dict(r))
            g = "\ufeff".encode("utf-8") + s.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{tablo}.csv"')
            self.send_header("Content-Length", str(len(g)))
            self.end_headers()
            self.wfile.write(g)
            return
        b.close()
        return self._json({"hata": "yok"}, 404)

    # ---------- POST ----------
    def do_POST(self):
        yol = urllib.parse.urlparse(self.path).path
        v = self._oku()
        if yol == "/api/track":
            b = baglan()
            b.execute("INSERT INTO ziyaretler(tarih, sayfa, ip) VALUES(?,?,?)",
                      (simdi(), str(v.get("sayfa") or "/")[:80], self._ip()))
            b.commit()
            b.close()
            return self._json({"ok": True})
        if yol == "/api/lead":
            ad = str(v.get("ad") or "").strip()[:80]
            tel = str(v.get("tel") or "").strip()[:30]
            if not ad or not tel:
                return self._json({"hata": "eksik"}, 400)
            b = baglan()
            b.execute("INSERT INTO talepler(tarih, ad, tel, urun, notlar) VALUES(?,?,?,?,?)",
                      (simdi(), ad, tel, str(v.get("urun") or "")[:80], str(v.get("not") or "")[:500]))
            b.commit()
            b.close()
            return self._json({"ok": True})
        if yol == "/api/admin/giris":
            if str(v.get("sifre") or "") == ADMIN_SIFRE:
                return self._json({"jeton": jeton_uret()})
            return self._json({"hata": "sifre"}, 401)
        if not self._yetki():
            return self._json({"hata": "yetki"}, 401)
        b = baglan()
        if yol == "/api/admin/talep-durum":
            b.execute("UPDATE talepler SET durum=? WHERE id=?", (v.get("durum"), v.get("id")))
            b.commit()
            b.close()
            return self._json({"ok": True})
        if yol == "/api/admin/talep-sil":
            b.execute("DELETE FROM talepler WHERE id=?", (v.get("id"),))
            b.commit()
            b.close()
            return self._json({"ok": True})
        if yol == "/api/admin/siparis-ekle":
            try:
                tutar = float(v.get("tutar") or 0)
            except (ValueError, TypeError):
                tutar = 0
            b.execute("""INSERT INTO siparisler(tarih, musteri, telefon, urun, tutar, durum, notlar)
                         VALUES(?,?,?,?,?,?,?)""",
                      (simdi(), v.get("musteri"), v.get("telefon"), v.get("urun"),
                       tutar, v.get("durum") or "bekliyor", v.get("notlar")))
            if v.get("talep_id"):
                b.execute("UPDATE talepler SET durum='satildi' WHERE id=?", (v.get("talep_id"),))
            b.commit()
            b.close()
            return self._json({"ok": True})
        if yol == "/api/admin/siparis-durum":
            b.execute("UPDATE siparisler SET durum=? WHERE id=?", (v.get("durum"), v.get("id")))
            b.commit()
            b.close()
            return self._json({"ok": True})
        if yol == "/api/admin/siparis-sil":
            b.execute("DELETE FROM siparisler WHERE id=?", (v.get("id"),))
            b.commit()
            b.close()
            return self._json({"ok": True})
        b.close()
        return self._json({"hata": "yok"}, 404)


if __name__ == "__main__":
    kur()
    srv = ThreadingHTTPServer(("127.0.0.1", 8000), El)
    print("Fu-Lin site:  http://localhost:8000")
    print("Admin panel:  http://localhost:8000/admin  (sifre: efe333)")
    srv.serve_forever()
