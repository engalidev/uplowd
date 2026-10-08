/* خريطة العراق التفاعلية.
   المصدر الأول: ملف GeoJSON رسمي (static/data/iraq-adm1.geojson) => حدود دقيقة.
   الاحتياطي: iraq-map.js (حدود تخطيطية تقريبية). */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg", DATA = window.IRAQ_DATA, ICONS = window.IRAQ_ICONS;
  var host = document.getElementById("iraqMap");
  if (!host || !DATA || !ICONS) return;
  var P = { box: byId("govCard"), icon: byId("govIcon"), name: byId("govName"), en: byId("govEn"), mark: byId("govMark"), desc: byId("govDesc") };
  var svg, hl, hlIcon, current = null, M, hue = {};
  function byId(i) { return document.getElementById(i); }
  function el(tag, a, parent) { var n = document.createElementNS(NS, tag); for (var k in a) n.setAttribute(k, a[k]); if (parent) parent.appendChild(n); return n; }
  function iconSvg(k) { return '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">' + (ICONS[k] || "") + "</svg>"; }

  /* ---------- GeoJSON -> نموذج الخريطة ---------- */
  function norm(s) { return String(s || "").toLowerCase().replace(/governorate|province|محافظة/g, "").replace(/[^a-z\u0600-\u06ff]/g, "").replace(/^(al|ال)/, ""); }
  function findId(name) {
    var n = norm(name); if (!n) return null;
    for (var i = 0; i < DATA.length; i++) {
      var al = (DATA[i].alias || []).concat([DATA[i].en, DATA[i].ar]);
      for (var j = 0; j < al.length; j++) { var a = norm(al[j]); if (a && (n === a || (n.length > 3 && (n.endsWith(a) || a.endsWith(n))))) return DATA[i].id; }
    }
    return null;
  }
  function fromGeoJSON(gj) {
    var feats = gj.features || [], minLon = 999, maxLon = -999, minLat = 999, maxLat = -999;
    function walk(c, f) { if (typeof c[0] === "number") f(c); else c.forEach(function (x) { walk(x, f); }); }
    feats.forEach(function (f) { walk(f.geometry.coordinates, function (p) { minLon = Math.min(minLon, p[0]); maxLon = Math.max(maxLon, p[0]); minLat = Math.min(minLat, p[1]); maxLat = Math.max(maxLat, p[1]); }); });
    var k = Math.cos(((minLat + maxLat) / 2) * Math.PI / 180), S = 880 / ((maxLon - minLon) * k), pad = 20;
    var pr = function (p) { return [(p[0] - minLon) * k * S + pad, (maxLat - p[1]) * S + pad]; };
    var geo = {}, unmatched = [];
    feats.forEach(function (f) {
      var pr0 = f.properties || {}, id = findId(pr0.shapeName || pr0.NAME_1 || pr0.ADM1_EN || pr0.name || pr0.NAME_EN || pr0.name_en || pr0.ADM1_AR || pr0.NL_NAME_1);
      if (!id) { unmatched.push(pr0.shapeName || pr0.NAME_1 || pr0.name); return; }
      var polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates, d = "", best = null, bestA = 0;
      polys.forEach(function (poly) {
        poly.forEach(function (ring, ri) {
          var pts = ring.map(pr); d += "M" + pts.map(function (q) { return q[0].toFixed(1) + "," + q[1].toFixed(1); }).join(" ") + "Z";
          if (ri === 0) { var a = 0, cx = 0, cy = 0; for (var i = 0; i < pts.length - 1; i++) { var w = pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]; a += w; cx += (pts[i][0] + pts[i + 1][0]) * w; cy += (pts[i][1] + pts[i + 1][1]) * w; }
            if (Math.abs(a) > bestA) { bestA = Math.abs(a); best = { x: cx / (3 * a), y: cy / (3 * a), pts: pts }; } }
        });
      });
      if (best && !inside(best.x, best.y, best.pts)) { var m = best.pts.reduce(function (s, q) { return [s[0] + q[0], s[1] + q[1]]; }, [0, 0]); best.x = m[0] / best.pts.length; best.y = m[1] / best.pts.length; }
      geo[id] = { d: (geo[id] ? geo[id].d : "") + d, x: best ? +best.x.toFixed(1) : 0, y: best ? +best.y.toFixed(1) : 0 };
    });
    if (unmatched.length) console.warn("[iraq-map] محافظات لم تُطابق أي اسم في iraq-data.js:", unmatched);
    var all = Object.keys(geo).map(function (i) { return geo[i].d; }).join("");
    return { viewBox: "0 0 " + Math.round((maxLon - minLon) * k * S + pad * 2) + " " + Math.round((maxLat - minLat) * S + pad * 2), outline: all, geo: geo, real: true };
  }
  function inside(x, y, pts) { var c = false; for (var i = 0, j = pts.length - 1; i < pts.length; j = i++) if ((pts[i][1] > y) !== (pts[j][1] > y) && x < (pts[j][0] - pts[i][0]) * (y - pts[i][1]) / (pts[j][1] - pts[i][1]) + pts[i][0]) c = !c; return c; }

  /* ---------- الرسم ---------- */
  function build() {
    svg = el("svg", { viewBox: M.viewBox, role: "group", "aria-label": "خريطة العراق التفاعلية" });
    svg.innerHTML = '<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="rgba(125,211,252,.16)"/></pattern></defs>';
    el("rect", { width: "100%", height: "100%", fill: "url(#dots)" }, svg);
    el("path", { d: M.outline, class: "outline", filter: "url(#glow)" }, svg);
    var layer = el("g", {}, svg), labels;
    DATA.forEach(function (g, i) {
      var geo = M.geo[g.id]; if (!geo) return;
      hue[g.id] = [190, 215, 255, 275][i % 4];
      var p = el("path", { d: geo.d, class: "gov", tabindex: "0", role: "button", "aria-label": g.ar }, layer);
      p.style.setProperty("--h", hue[g.id]); p.style.setProperty("--i", i);
      p.addEventListener("pointerenter", function (e) { if (e.pointerType !== "touch") show(g.id); });
      p.addEventListener("click", function () { show(g.id); });
      p.addEventListener("focus", function () { show(g.id); });
    });
    labels = el("g", { class: "labels" }, svg);
    DATA.forEach(function (g) { var geo = M.geo[g.id]; if (!geo) return; el("text", { x: geo.x, y: geo.y + 4, "text-anchor": "middle", "data-id": g.id }, labels).textContent = g.ar; });
    hl = el("path", { class: "hl", d: "" }, svg); hlIcon = el("g", { class: "hl-icon" }, svg);
    svg.addEventListener("pointerleave", function (e) { if (e.pointerType !== "touch") clear(); });
    host.innerHTML = ""; host.appendChild(svg);
  }
  function show(id) {
    var g = DATA.filter(function (x) { return x.id === id; })[0], geo = M.geo[id]; if (!g || !geo || current === id) return; current = id;
    hl.setAttribute("d", geo.d); hl.style.setProperty("--h", hue[id]); hl.classList.add("on");
    hlIcon.setAttribute("transform", "translate(" + (geo.x - 26) + "," + (geo.y - 58) + ") scale(.8)");
    hlIcon.innerHTML = '<g class="pop"><circle cx="32" cy="32" r="31" class="bub"/>' + (ICONS[g.icon] || "") + "</g>";
    Array.prototype.forEach.call(svg.querySelectorAll("text"), function (t) { t.classList.toggle("dim", t.getAttribute("data-id") === id); });
    P.box.classList.remove("swap"); void P.box.offsetWidth; P.box.classList.add("swap", "has");
    P.icon.innerHTML = iconSvg(g.icon); P.name.textContent = g.ar; P.en.textContent = g.en; P.mark.textContent = g.landmark; P.desc.textContent = g.desc;
  }
  function clear() {
    current = null; hl.classList.remove("on"); hlIcon.innerHTML = "";
    Array.prototype.forEach.call(svg.querySelectorAll("text.dim"), function (t) { t.classList.remove("dim"); });
    P.box.classList.remove("has", "swap"); P.icon.innerHTML = iconSvg("dome");
    P.name.textContent = "العراق"; P.en.textContent = "Iraq"; P.mark.textContent = Object.keys(M.geo).length + " محافظة";
    P.desc.textContent = "مرّر المؤشر فوق أي محافظة لاكتشاف رمزها التاريخي والحضاري.";
  }
  function start(m) { if (!m) { host.textContent = "تعذّر تحميل بيانات الخريطة."; return; } M = m; build(); clear(); if (!m.real) host.insertAdjacentHTML("beforeend", ""); }

  fetch(host.dataset.geojson, { cache: "force-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (gj) { start(fromGeoJSON(gj)); })
    .catch(function () { start(window.IRAQ_MAP); });
})();
