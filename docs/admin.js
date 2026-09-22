// Fu-Lin admin paneli
(function () {
  "use strict";
  var jeton = localStorage.getItem("fulin_jeton") || "";
  var seciliTalep = null;

  function api(yol, veri, metot) {
    return fetch(yol, {
      method: metot || (veri ? "POST" : "GET"),
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + jeton },
      body: veri ? JSON.stringify(veri) : undefined
    }).then(function (r) {
      if (r.status === 401) { cikis(); throw new Error("yetki"); }
      return r.json();
    });
  }

  function para(x) {
    return Number(x || 0).toLocaleString("tr-TR", { minimumFractionDigits: 2 }) + " ₺";
  }

  // giriş
  function giris() {
    var s = document.getElementById("sifre").value;
    fetch("/api/admin/giris", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sifre: s }) }).then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.jeton) {
          jeton = j.jeton;
          localStorage.setItem("fulin_jeton", jeton);
          ac();
        } else {
          document.getElementById("girisHata").textContent = "Hatalı şifre!";
        }
      });
  }
  document.getElementById("girisBtn").addEventListener("click", giris);
  document.getElementById("sifre").addEventListener("keydown", function (e) { if (e.key === "Enter") giris(); });

  function cikis() {
    jeton = "";
    localStorage.removeItem("fulin_jeton");
    document.getElementById("panel").style.display = "none";
    document.getElementById("giris").style.display = "flex";
  }
  document.getElementById("cikis").addEventListener("click", cikis);

  // sekmeler
  document.querySelectorAll("#panel nav button[data-sekme]").forEach(function (b) {
    b.addEventListener("click", function () {
      document.querySelectorAll("#panel nav button").forEach(function (x) { x.classList.remove("aktif"); });
      b.classList.add("aktif");
      document.querySelectorAll(".sekme").forEach(function (s) { s.style.display = "none"; });
      document.getElementById("sekme-" + b.dataset.sekme).style.display = "block";
      if (b.dataset.sekme === "talepler") talepleriYukle();
      if (b.dataset.sekme === "siparisler") siparisleriYukle();
    });
  });

  function ac() {
    document.getElementById("giris").style.display = "none";
    document.getElementById("panel").style.display = "block";
    ozetYukle();
  }

  function ozetYukle() {
    api("/api/admin/ozet").then(function (o) {
      document.getElementById("kZiyaret").textContent = o.ziyaret;
      document.getElementById("kBugun").textContent = "bugün: " + o.bugun;
      document.getElementById("kTalep").textContent = o.talep;
      document.getElementById("kYeni").textContent = o.yeni + " yeni";
      document.getElementById("kIndirme").textContent = o.indirme;
      document.getElementById("kSiparis").textContent = o.siparis;
      document.getElementById("kCiro").textContent = "tahsilat: " + para(o.ciro);
      document.getElementById("yeniRozet").textContent = o.yeni ? o.yeni : "";
      var maks = 1;
      o.gunler.forEach(function (g) { maks = Math.max(maks, g.ziyaret); });
      document.getElementById("grafik").innerHTML = o.gunler.map(function (g) {
        return '<div class="bar"><div class="dolgu" style="height:' +
          Math.round((g.ziyaret / maks) * 110) + 'px" title="' + g.ziyaret + '"></div><small>' + g.gun + "</small></div>";
      }).join("");
      document.getElementById("durumlar").innerHTML = o.durumlar.map(function (d) {
        return '<span class="cip"><span class="dot ' + d.durum + '"></span>' + d.durum + ": <b>" + d.n + "</b></span>";
      }).join("") || '<small style="color:#93a1b8">Henüz talep yok.</small>';
    }).catch(function () {});
  }

  function talepleriYukle() {
    api("/api/admin/talepler").then(function (rows) {
      document.getElementById("talepSatir").innerHTML = rows.map(function (r) {
        return "<tr><td>" + r.tarih + "</td><td>" + esc(r.ad) + "</td><td>" + esc(r.tel) +
          "</td><td>" + esc(r.urun) + "</td><td>" + esc(r.notlar) +
          '</td><td><select data-id="' + r.id + '" class="durumSec">' +
          ["yeni", "arandi", "satildi", "olumsuz"].map(function (d) {
            return '<option value="' + d + '"' + (d === r.durum ? " selected" : "") + ">" + d + "</option>";
          }).join("") + "</select></td><td>" +
          '<button class="sat" data-sip="' + r.id + '" data-ad="' + esc(r.ad) + '" data-tel="' + esc(r.tel) +
          '" data-urun="' + esc(r.urun) + '">Siparişe çevir</button>' +
          '<button data-sil="' + r.id + '">Sil</button></td></tr>';
      }).join("");
      document.querySelectorAll(".durumSec").forEach(function (s) {
        s.addEventListener("change", function () {
          api("/api/admin/talep-durum", { id: s.dataset.id, durum: s.value }).then(ozetYukle);
        });
      });
      document.querySelectorAll("[data-sil]").forEach(function (b) {
        b.addEventListener("click", function () {
          if (confirm("Talep silinsin mi?")) api("/api/admin/talep-sil", { id: b.dataset.sil }).then(function () { talepleriYukle(); ozetYukle(); });
        });
      });
      document.querySelectorAll("[data-sip]").forEach(function (b) {
        b.addEventListener("click", function () {
          seciliTalep = b.dataset.sip;
          document.getElementById("sMusteri").value = b.dataset.ad;
          document.getElementById("sTel").value = b.dataset.tel;
          document.getElementById("sUrun").value = b.dataset.urun || "Diş Klinik Yönetim";
          document.getElementById("siparisModal").style.display = "flex";
        });
      });
    });
  }

  function siparisleriYukle() {
    api("/api/admin/siparisler").then(function (rows) {
      document.getElementById("siparisSatir").innerHTML = rows.map(function (r) {
        return "<tr><td>" + r.tarih + "</td><td>" + esc(r.musteri) + "</td><td>" + esc(r.telefon) +
          "</td><td>" + esc(r.urun) + "</td><td>" + para(r.tutar) +
          '</td><td><select data-id="' + r.id + '" class="sipDurum">' +
          ["bekliyor", "odendi", "iptal"].map(function (d) {
            return '<option value="' + d + '"' + (d === r.durum ? " selected" : "") + ">" + d + "</option>";
          }).join("") + "</select></td><td>" +
          '<button data-ssil="' + r.id + '">Sil</button></td></tr>';
      }).join("");
      document.querySelectorAll(".sipDurum").forEach(function (s) {
        s.addEventListener("change", function () {
          api("/api/admin/siparis-durum", { id: s.dataset.id, durum: s.value }).then(ozetYukle);
        });
      });
      document.querySelectorAll("[data-ssil]").forEach(function (b) {
        b.addEventListener("click", function () {
          if (confirm("Sipariş silinsin mi?")) api("/api/admin/siparis-sil", { id: b.dataset.ssil }).then(function () { siparisleriYukle(); ozetYukle(); });
        });
      });
    });
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  document.getElementById("siparisEkleBtn").addEventListener("click", function () {
    seciliTalep = null;
    document.getElementById("siparisModal").style.display = "flex";
  });
  document.getElementById("sVazgec").addEventListener("click", function () {
    document.getElementById("siparisModal").style.display = "none";
  });
  document.getElementById("sKaydet").addEventListener("click", function () {
    api("/api/admin/siparis-ekle", {
      talep_id: seciliTalep, musteri: document.getElementById("sMusteri").value,
      telefon: document.getElementById("sTel").value, urun: document.getElementById("sUrun").value,
      tutar: document.getElementById("sTutar").value, durum: document.getElementById("sDurum").value,
      notlar: document.getElementById("sNot").value
    }).then(function () {
      document.getElementById("siparisModal").style.display = "none";
      siparisleriYukle(); ozetYukle();
    });
  });

  // CSV bağlantılarına jeton taşı (dosya indirme fetch ile olmaz)
  ["csvT", "csvS"].forEach(function (id) {
    document.getElementById(id).addEventListener("click", function (e) {
      e.preventDefault();
      fetch(e.target.href, { headers: { "Authorization": "Bearer " + jeton } }).then(function (r) { return r.blob(); })
        .then(function (b) {
          var a = document.createElement("a");
          a.href = URL.createObjectURL(b);
          a.download = id === "csvT" ? "talepler.csv" : "siparisler.csv";
          a.click();
        });
    });
  });

  if (jeton) ac();
})();
