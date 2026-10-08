/* الصفحة الرئيسية — الخريطة التفاعلية (يعتمد على iraq-map.js و iraq-data.js) */
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg", M = window.IRAQ_MAP, DATA = window.IRAQ_DATA, ICONS = window.IRAQ_ICONS;
  var host = document.getElementById("iraqMap");
  if (!host || !M || !DATA) return;

  var panel = {
    box: document.getElementById("govCard"), icon: document.getElementById("govIcon"),
    name: document.getElementById("govName"), en: document.getElementById("govEn"),
    mark: document.getElementById("govMark"), desc: document.getElementById("govDesc")
  };
  var svg, hl, hlIcon, current = null, byId = {};

  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function icon(key) { return '<svg viewBox="0 0 64 64" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">' + (ICONS[key] || "") + "</svg>"; }

  function build() {
    svg = el("svg", { viewBox: M.viewBox, role: "group", "aria-label": "خريطة العراق التفاعلية" });
    svg.innerHTML =
      '<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="6" result="b"/>' +
      '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
      '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1" fill="rgba(125,211,252,.18)"/></pattern></defs>';
    el("rect", { width: "100%", height: "100%", fill: "url(#dots)" }, svg);
    el("path", { d: M.outline, class: "outline", filter: "url(#glow)" }, svg);

    var layer = el("g", { class: "govs" }, svg);
    DATA.forEach(function (g, i) {
      var geo = M.geo[g.id]; if (!geo) return;
      byId[g.id] = { data: g, geo: geo };
      var p = el("path", { d: geo.d, class: "gov", tabindex: "0", "data-id": g.id, role: "button", "aria-label": g.ar }, layer);
      p.style.setProperty("--h", [190, 215, 255, 275][i % 4]);
      p.style.setProperty("--i", i);
      p.addEventListener("pointerenter", function (e) { if (e.pointerType !== "touch") show(g.id); });
      p.addEventListener("click", function () { show(g.id); });
      p.addEventListener("focus", function () { show(g.id); });
    });

    var labels = el("g", { class: "labels" }, svg);
    DATA.forEach(function (g) {
      var geo = M.geo[g.id]; if (!geo) return;
      var t = el("text", { x: geo.x, y: geo.y + 4, "text-anchor": "middle", "data-id": g.id }, labels);
      t.textContent = g.ar;
    });

    hl = el("path", { class: "hl", d: "" }, svg);
    hlIcon = el("g", { class: "hl-icon" }, svg);
    svg.addEventListener("pointerleave", function (e) { if (e.pointerType !== "touch") clear(); });
    host.appendChild(svg);
  }

  function show(id) {
    if (current === id) return;
    var r = byId[id]; if (!r) return;
    current = id;
    hl.setAttribute("d", r.geo.d);
    hl.style.setProperty("--h", svg.querySelector('.gov[data-id="' + id + '"]').style.getPropertyValue("--h"));
    hl.classList.add("on");
    hlIcon.setAttribute("transform", "translate(" + (r.geo.x - 26) + "," + (r.geo.y - 58) + ") scale(.8)");
    hlIcon.innerHTML = '<g class="pop"><circle cx="32" cy="32" r="31" class="bub"/>' + (ICONS[r.data.icon] || "") + "</g>";
    Array.prototype.forEach.call(svg.querySelectorAll("text"), function (t) { t.classList.toggle("dim", t.dataset.id === id); });

    panel.box.classList.remove("swap"); void panel.box.offsetWidth; panel.box.classList.add("swap", "has");
    panel.icon.innerHTML = icon(r.data.icon);
    panel.name.textContent = r.data.ar; panel.en.textContent = r.data.en;
    panel.mark.textContent = r.data.landmark; panel.desc.textContent = r.data.desc;
  }

  function clear() {
    current = null;
    hl.classList.remove("on"); hlIcon.innerHTML = "";
    Array.prototype.forEach.call(svg.querySelectorAll("text.dim"), function (t) { t.classList.remove("dim"); });
    panel.box.classList.remove("has", "swap");
    panel.icon.innerHTML = icon("palm").replace(/<path.*<\/svg>/, "") + "</svg>";
    panel.name.textContent = "العراق"; panel.en.textContent = "Iraq";
    panel.mark.textContent = "١٨ محافظة"; panel.desc.textContent = "مرّر المؤشر فوق أي محافظة لاكتشاف رمزها التاريخي والحضاري.";
  }

  build(); clear();
})();
