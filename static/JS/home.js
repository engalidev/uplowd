/* خريطة العراق التفاعلية — حدود رسمية (GeoJSON) + نهرا دجلة والفرات + معالم تخرج من الأرض.
   يعتمد على: iraq-art.js · iraq-data.js · iraq-rivers.js  (واحتياطيًا iraq-map.js) */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg", DATA = window.IRAQ_DATA, ART = window.IRAQ_ART, RIV = window.IRAQ_RIVERS || [];
  var host = document.getElementById("iraqMap");
  if (!host || !DATA || !ART) return;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches, uid = 0;
  var $ = function (i) { return document.getElementById(i); };
  var P = { box: $("govCard"), icon: $("govIcon"), name: $("govName"), en: $("govEn"), mark: $("govMark"), desc: $("govDesc") };
  var svg, hl, hlArt, cardSvg, current = null, M, hue = {};

  function el(tag, a, parent) { var n = document.createElementNS(NS, tag); for (var k in a) n.setAttribute(k, a[k]); if (parent) parent.appendChild(n); return n; }
  var clamp = function (v) { return Math.max(0, Math.min(1, v)); };
  var back = function (x) { var c = 1.1; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };

  /* ================= ظهور المعلم من الأرض مع الغبار ================= */
  function emerge(root, key, still) {
    cancelAnimationFrame(root._raf);
    var id = "clp" + (++uid);
    root.innerHTML = '<clipPath id="' + id + '"><rect x="-60" y="-80" width="240" height="176"/></clipPath>' +
      '<ellipse class="shadow" cx="60" cy="97" rx="46" ry="4"/><ellipse class="ring" cx="60" cy="96" rx="6" ry="2"/>' +
      '<g clip-path="url(#' + id + ')"><g class="art">' + (ART[key] || "") + '</g></g><g class="dust"></g>';
    var art = root.querySelector(".art"), ring = root.querySelector(".ring"), shadow = root.querySelector(".shadow"), dust = root.querySelector(".dust"), ps = [], i;
    if (still || reduce) { ring.style.display = "none"; return; }
    for (i = 0; i < 22; i++) ps.push({ c: el("circle", { class: "dp", r: 3, opacity: 0 }, dust), x: 6 + Math.random() * 108, d: Math.random() * .4, vy: 12 + Math.random() * 30, vx: (Math.random() - .5) * 30, r: 3 + Math.random() * 6 });
    var t0 = null, dur = 1700;
    (function frame(t) {
      if (t0 === null) t0 = t;
      var k = clamp((t - t0) / dur), e = back(clamp(k / .78)), sh = Math.sin((t - t0) * .09) * (1 - clamp(k / .6)) * 1.8;
      art.setAttribute("transform", "translate(" + sh.toFixed(2) + " " + ((1 - e) * 104).toFixed(2) + ")");
      shadow.setAttribute("opacity", clamp(k * 2).toFixed(2));
      ring.setAttribute("rx", (6 + 56 * clamp(k / .7)).toFixed(1)); ring.setAttribute("ry", (2 + 7 * clamp(k / .7)).toFixed(1)); ring.setAttribute("opacity", (.9 * (1 - clamp(k / .7))).toFixed(2));
      ps.forEach(function (p) {
        var q = clamp((k - p.d) / .6);
        if (q <= 0 || q >= 1) { p.c.setAttribute("opacity", 0); return; }
        var up = 1 - Math.pow(1 - q, 2);
        p.c.setAttribute("cx", (p.x + p.vx * up).toFixed(1)); p.c.setAttribute("cy", (97 - p.vy * up).toFixed(1));
        p.c.setAttribute("r", (p.r * (.4 + q * 1.7)).toFixed(1)); p.c.setAttribute("opacity", (.6 * Math.pow(1 - q, 1.3)).toFixed(2));
      });
      if (k < 1) root._raf = requestAnimationFrame(frame); else art.setAttribute("transform", "translate(0 0)");
    })(performance.now());
  }

  /* ================= GeoJSON → نموذج الخريطة ================= */
  function norm(s) { return String(s || "").toLowerCase().replace(/governorate|province|محافظة/g, "").replace(/[^a-z\u0600-\u06ff]/g, "").replace(/^(al|ال)/, ""); }
  function findId(name) {
    var n = norm(name); if (!n) return null;
    for (var i = 0; i < DATA.length; i++) {
      var al = (DATA[i].alias || []).concat([DATA[i].en, DATA[i].ar]);
      for (var j = 0; j < al.length; j++) { var a = norm(al[j]); if (a && (n === a || (n.length > 3 && (n.endsWith(a) || a.endsWith(n))))) return DATA[i].id; }
    }
    return null;
  }
  function inside(x, y, pts) { var c = false; for (var i = 0, j = pts.length - 1; i < pts.length; j = i++) if ((pts[i][1] > y) !== (pts[j][1] > y) && x < (pts[j][0] - pts[i][0]) * (y - pts[i][1]) / (pts[j][1] - pts[i][1]) + pts[i][0]) c = !c; return c; }
  function fromGeoJSON(gj) {
    var feats = gj.features || [], minLon = 999, maxLon = -999, minLat = 999, maxLat = -999;
    (function walk(c) { if (typeof c[0] === "number") { minLon = Math.min(minLon, c[0]); maxLon = Math.max(maxLon, c[0]); minLat = Math.min(minLat, c[1]); maxLat = Math.max(maxLat, c[1]); } else c.forEach(walk); })(feats.map(function (f) { return f.geometry.coordinates; }));
    var k = Math.cos(((minLat + maxLat) / 2) * Math.PI / 180), S = 880 / ((maxLon - minLon) * k), pad = 20;
    var proj = function (lon, lat) { return [(lon - minLon) * k * S + pad, (maxLat - lat) * S + pad]; };
    var geo = {}, unmatched = [];
    feats.forEach(function (f) {
      var pr = f.properties || {}, id = findId(pr.shapeName || pr.NAME_1 || pr.ADM1_EN || pr.name || pr.name_en || pr.ADM1_AR || pr.NL_NAME_1);
      if (!id) { unmatched.push(pr.shapeName || pr.NAME_1 || pr.name); return; }
      var polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates, d = "", best = null, bestA = 0;
      polys.forEach(function (poly) { poly.forEach(function (ring, ri) {
        var pts = ring.map(function (p) { return proj(p[0], p[1]); });
        d += "M" + pts.map(function (q) { return q[0].toFixed(1) + "," + q[1].toFixed(1); }).join(" ") + "Z";
        if (ri) return;
        var a = 0, cx = 0, cy = 0; for (var i = 0; i < pts.length - 1; i++) { var w = pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]; a += w; cx += (pts[i][0] + pts[i + 1][0]) * w; cy += (pts[i][1] + pts[i + 1][1]) * w; }
        if (Math.abs(a) > bestA) { bestA = Math.abs(a); best = { x: cx / (3 * a), y: cy / (3 * a), pts: pts }; }
      }); });
      if (best && !inside(best.x, best.y, best.pts)) { var m = best.pts.reduce(function (s, q) { return [s[0] + q[0], s[1] + q[1]]; }, [0, 0]); best.x = m[0] / best.pts.length; best.y = m[1] / best.pts.length; }
      geo[id] = { d: (geo[id] ? geo[id].d : "") + d, x: best ? +best.x.toFixed(1) : 0, y: best ? +best.y.toFixed(1) : 0 };
    });
    if (unmatched.length) console.warn("[iraq-map] أسماء لم تُطابق iraq-data.js:", unmatched);
    return { viewBox: "0 0 " + Math.round((maxLon - minLon) * k * S + pad * 2) + " " + Math.round((maxLat - minLat) * S + pad * 2),
      outline: Object.keys(geo).map(function (i) { return geo[i].d; }).join(""), geo: geo, proj: proj, real: true };
  }
  function fallback() {
    var m = window.IRAQ_MAP; if (!m) return null; var c = Math.cos(33.5 * Math.PI / 180);
    m.proj = function (lon, lat) { return [(lon - 38.5) * c * 100 + 20, (37.6 - lat) * 100 + 20]; }; return m;
  }

  /* ================= الأنهار ================= */
  function smooth(pts) {
    var f = function (n) { return n.toFixed(1); }, d = "M" + f(pts[0][0]) + "," + f(pts[0][1]);
    for (var i = 0; i < pts.length - 1; i++) {
      var p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
      d += "C" + f(p1[0] + (p2[0] - p0[0]) / 6) + "," + f(p1[1] + (p2[1] - p0[1]) / 6) + " " + f(p2[0] - (p3[0] - p1[0]) / 6) + "," + f(p2[1] - (p3[1] - p1[1]) / 6) + " " + f(p2[0]) + "," + f(p2[1]);
    }
    return d;
  }
  function drawRivers(parent) {
    var g = el("g", { class: "rivers" }, parent), lg = el("g", { class: "rlabels" }, parent);
    RIV.forEach(function (r) {
      var pts = r.pts.map(function (p) { return M.proj(p[0], p[1]); }), d = smooth(pts);
      var b = el("path", { d: d, class: "riv-b", pathLength: 1 }, g); b.style.color = r.color; b.style.setProperty("--d", r.delay + "s");
      var fl = el("path", { d: d, class: "riv-f" }, g); fl.style.setProperty("--d", r.delay + "s");
      if (r.label) { var q = M.proj(r.label[0], r.label[1]), t = el("text", { x: q[0] + r.label[2], y: q[1] + r.label[3], class: "rname" }, lg); t.textContent = r.ar; t.style.setProperty("--d", r.delay + "s"); t.style.fill = r.color; }
    });
  }

  /* ================= الرسم والتفاعل ================= */
  function build() {
    svg = el("svg", { viewBox: M.viewBox, role: "group", "aria-label": "خريطة العراق التفاعلية" });
    svg.innerHTML = '<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="rgba(125,211,252,.16)"/></pattern></defs>';
    el("rect", { width: "100%", height: "100%", fill: "url(#dots)" }, svg);
    el("path", { d: M.outline, class: "outline", filter: "url(#glow)" }, svg);
    var layer = el("g", {}, svg);
    DATA.forEach(function (g, i) {
      var geo = M.geo[g.id]; if (!geo) return;
      hue[g.id] = [190, 215, 255, 275][i % 4];
      var p = el("path", { d: geo.d, class: "gov", tabindex: "0", role: "button", "aria-label": g.ar }, layer);
      p.style.setProperty("--h", hue[g.id]); p.style.setProperty("--i", i);
      p.addEventListener("pointerenter", function (e) { if (e.pointerType !== "touch") show(g.id); });
      p.addEventListener("click", function () { show(g.id); });
      p.addEventListener("focus", function () { show(g.id); });
    });
    drawRivers(svg);
    var labels = el("g", { class: "labels" }, svg);
    DATA.forEach(function (g) { var geo = M.geo[g.id]; if (!geo) return; el("text", { x: geo.x, y: geo.y + 4, "text-anchor": "middle", "data-id": g.id }, labels).textContent = g.ar; });
    hl = el("path", { class: "hl", d: "" }, svg); hlArt = el("g", { class: "map-art" }, svg);
    svg.addEventListener("pointerleave", function (e) { if (e.pointerType !== "touch") clear(); });
    host.innerHTML = ""; host.appendChild(svg);
    P.icon.innerHTML = ""; cardSvg = el("svg", { viewBox: "0 0 120 100", class: "card-art" }, P.icon);
  }
  function show(id) {
    var g = DATA.filter(function (x) { return x.id === id; })[0], geo = M.geo[id]; if (!g || !geo || current === id) return; current = id;
    hl.setAttribute("d", geo.d); hl.style.setProperty("--h", hue[id]); hl.classList.add("on");
    hlArt.setAttribute("transform", "translate(" + (geo.x - 66) + "," + (geo.y - 100) + ") scale(1.1)"); emerge(hlArt, g.art);
    Array.prototype.forEach.call(svg.querySelectorAll(".labels text"), function (t) { t.classList.toggle("dim", t.getAttribute("data-id") === id); });
    P.box.classList.remove("swap"); void P.box.offsetWidth; P.box.classList.add("swap", "has");
    emerge(cardSvg, g.art); P.name.textContent = g.ar; P.en.textContent = g.en; P.mark.textContent = g.landmark; P.desc.textContent = g.desc;
  }
  function clear() {
    current = null; hl.classList.remove("on"); cancelAnimationFrame(hlArt._raf); hlArt.innerHTML = "";
    Array.prototype.forEach.call(svg.querySelectorAll(".labels text.dim"), function (t) { t.classList.remove("dim"); });
    P.box.classList.remove("has", "swap"); emerge(cardSvg, "pin", true);
    P.name.textContent = "العراق"; P.en.textContent = "Iraq"; P.mark.textContent = Object.keys(M.geo).length + " محافظة";
    P.desc.textContent = "مرّر المؤشر فوق أي محافظة لتشاهد معلمها يخرج من الأرض، وتتبّع مجرى دجلة والفرات.";
  }
  function start(m) { if (!m) { host.textContent = "تعذّر تحميل بيانات الخريطة."; return; } M = m; build(); clear(); }

  fetch(host.dataset.geojson, { cache: "force-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (gj) { start(fromGeoJSON(gj)); })
    .catch(function () { start(fallback()); });
})();
