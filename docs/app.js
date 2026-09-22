// Fu-Lin site etkileşimleri
(function () {
  "use strict";

  // mobil menü
  var btn = document.getElementById("menuBtn");
  var mm = document.getElementById("mobileMenu");
  btn.addEventListener("click", function () { mm.classList.toggle("open"); });
  mm.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () { mm.classList.remove("open"); });
  });

  // daktilo efekti
  var words = ["günler içinde.", "size özel.", "tek kurulumla."];
  var el = document.getElementById("typed");
  var wi = 0, ci = 0, del = false;
  (function tick() {
    var w = words[wi];
    el.textContent = w.slice(0, ci);
    if (!del && ci < w.length) { ci++; return setTimeout(tick, 70); }
    if (!del && ci === w.length) { del = true; return setTimeout(tick, 1600); }
    if (del && ci > 0) { ci--; return setTimeout(tick, 34); }
    del = false; wi = (wi + 1) % words.length;
    setTimeout(tick, 350);
  })();

  // scroll reveal
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach(function (n) { io.observe(n); });

  // sayaçlar
  var cio = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      var n = e.target, to = +n.dataset.to, t0 = null;
      cio.unobserve(n);
      (function step(t) {
        if (!t0) t0 = t;
        var p = Math.min((t - t0) / 1400, 1);
        n.textContent = Math.round(to * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      })(performance.now());
    });
  }, { threshold: 0.5 });
  document.querySelectorAll(".counter").forEach(function (n) { cio.observe(n); });

  // hero kart eğilme
  var tilt = document.querySelector(".tilt");
  if (tilt && matchMedia("(pointer:fine)").matches) {
    document.querySelector(".hero-visual").addEventListener("mousemove", function (ev) {
      var r = tilt.getBoundingClientRect();
      var x = (ev.clientX - r.left) / r.width - 0.5;
      var y = (ev.clientY - r.top) / r.height - 0.5;
      tilt.style.transform = "perspective(900px) rotateY(" + (x * 8) + "deg) rotateX(" + (-y * 8) + "deg)";
    });
    document.querySelector(".hero-visual").addEventListener("mouseleave", function () {
      tilt.style.transform = "";
    });
  }

  // fiyat: ürün seçimine göre liste
  var FIYAT = {
    dis: [
      { t: "Tek Klinik", f: "₺12.900", d: "Tek bilgisayar, tek klinik. Ömür boyu kullanım + 1 yıl destek.", tag: null, b: "Seç", stil: "ghost" },
      { t: "Pro + SMS", f: "₺22.900", d: "3 bilgisayar, NetGSM kurulumu, logo + şablon uyarlaması dahil.", tag: "Popüler", b: "Seç", stil: "primary" },
      { t: "Zincir / Özel", f: "Teklif", d: "Çok şubeli yapılara özel çok kullanıcılı sürüm ve eğitim.", tag: null, b: "Görüşelim", stil: "ghost" }
    ],
    tamir: [
      { t: "Tek Servis", f: "₺9.900", d: "Tek bilgisayar. Elektronik, otomotiv veya telefon-PC profilinden biri. Ömür boyu + 1 yıl destek.", tag: null, b: "Seç", stil: "ghost" },
      { t: "Pro", f: "₺14.900", d: "3 bilgisayar, logo uyarlaması, fatura belgesi kurulumu, öncelikli destek.", tag: "Popüler", b: "Seç", stil: "primary" },
      { t: "Zincir / Özel", f: "Teklif", d: "Çok şubeli servislere özel çok kullanıcılı sürüm ve eğitim.", tag: null, b: "Görüşelim", stil: "ghost" }
    ],
    teknik: [
      { t: "Tek Servis", f: "₺9.900", d: "Tek bilgisayar. Servis kaydı, form, garanti takibi, teknisyen kadrosu. Ömür boyu + 1 yıl destek.", tag: null, b: "Seç", stil: "ghost" },
      { t: "Pro", f: "₺14.900", d: "3 bilgisayar, logo uyarlaması, öncelikli destek ve eğitim.", tag: "Popüler", b: "Seç", stil: "primary" },
      { t: "Zincir / Özel", f: "Teklif", d: "Çok şubeli servislere özel çok kullanıcılı sürüm ve eğitim.", tag: null, b: "Görüşelim", stil: "ghost" }
    ]
  };
  function escH(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  }
  function fiyatCiz(urun) {
    var kutu = document.getElementById("fiyatKartlar");
    if (!kutu) return;
    kutu.innerHTML = FIYAT[urun].map(function (p) {
      return '<article class="card in' + (p.tag ? " featured" : "") + '">' +
        (p.tag ? '<div class="tag">' + p.tag + "</div>" : "") +
        "<h3>" + escH(p.t) + '</h3><b class="big">' + escH(p.f) + "</b><p>" + escH(p.d) + "</p>" +
        '<a class="btn ' + p.stil + ' full" href="#iletisim">' + p.b + "</a></article>";
    }).join("");
    document.querySelectorAll("#fiyatSec button").forEach(function (b) {
      b.classList.toggle("aktif", b.dataset.urun === urun);
    });
  }
  document.querySelectorAll("#fiyatSec button").forEach(function (b) {
    b.addEventListener("click", function () { fiyatCiz(b.dataset.urun); });
  });
  fiyatCiz("dis");

  // panel bağlantısı: site server.py ile mi açılıyor? (dosyaya çift tık = file://, panel çalışmaz)
  var panelAktif = location.protocol.indexOf("http") === 0;

  function kuyrukAl() {
    try { return JSON.parse(localStorage.getItem("fulin_bekleyen") || "[]"); }
    catch (e) { return []; }
  }
  function kuyrukKaydet(k) {
    try { localStorage.setItem("fulin_bekleyen", JSON.stringify(k)); } catch (e) {}
  }
  function leadPost(kayit) {
    return fetch("/api/lead", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(kayit) }).then(function (r) {
      if (!r.ok) throw new Error("kotu cevap");
      return true;
    });
  }
  function kuyruguBosalt() {
    var k = kuyrukAl();
    if (!k.length) return;
    var gonder = function (i) {
      if (i >= k.length) { kuyrukKaydet([]); return; }
      leadPost(k[i]).then(function () { gonder(i + 1); }, function () { kuyrukKaydet(k.slice(i)); });
    };
    gonder(0);
  }

  // ziyaret sayacı + bekleyen talepleri gönder (sadece sunucu modunda)
  if (panelAktif) {
    fetch("/api/track", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sayfa: location.pathname }) }).catch(function () {});
    kuyruguBosalt();
  }

  // form: önce panele kaydet, sonra talebi WhatsApp'a düşür
  document.getElementById("leadForm").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var data = new FormData(ev.target);
    var kayit = { ad: data.get("ad"), tel: data.get("tel"), urun: data.get("urun"), not: data.get("not") };
    var notEl = document.getElementById("formNote");
    var waAc = function () {
      var msg = "Merhaba, Fu-Lin demo istiyorum.%0AAd: " + encodeURIComponent((data.get("ad") || "").toString()) +
        "%0ATel: " + encodeURIComponent((data.get("tel") || "").toString()) +
        "%0AÜrün: " + encodeURIComponent((data.get("urun") || "").toString()) +
        "%0ANot: " + encodeURIComponent((data.get("not") || "").toString());
      window.open("https://wa.me/905511947840?text=" + msg, "_blank");
      ev.target.reset();
    };
    if (!panelAktif) {
      notEl.textContent = "⚠️ Site sunucusuz açıldı, talebin panele düşmedi. WhatsApp'tan göndermen yeterli.";
      waAc();
      return;
    }
    leadPost(kayit).then(function () {
      kuyruguBosalt();
      notEl.textContent = "Talebin panele kaydedildi ✅ WhatsApp açılıyor, gönder tuşuna basman yeterli.";
      waAc();
    }, function () {
      var k = kuyrukAl();
      k.push(kayit);
      kuyrukKaydet(k);
      notEl.textContent = "⚠️ Sunucuya ulaşılamadı, talep sıraya alındı. WhatsApp'tan göndermen yeterli.";
      waAc();
    });
  });
})();
