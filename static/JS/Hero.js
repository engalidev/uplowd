/* اللوحة البصرية المتحركة: شبكة جسيمات + لوحة تحكم حيّة */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (id) { return document.getElementById(id); };

  /* ---- 1) شبكة الجسيمات ---- */
  var cv = $("bgNet");
  if (cv && !reduce) {
    var ctx = cv.getContext("2d"), dpr = Math.min(window.devicePixelRatio || 1, 2), W, H, P = [], run = false, mx = -999, my = -999;
    var size = function () {
      var r = cv.parentNode.getBoundingClientRect(); W = r.width; H = r.height;
      cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      P = []; for (var i = 0, n = Math.min(90, Math.round(W * H / 14000)); i < n; i++)
        P.push({ x: Math.random() * W, y: Math.random() * H, vx: (Math.random() - .5) * .4, vy: (Math.random() - .5) * .4 });
    };
    var tick = function () {
      if (!run) return;
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < P.length; i++) {
        var p = P[i]; p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1;
        ctx.fillStyle = "rgba(34,211,238,.8)"; ctx.beginPath(); ctx.arc(p.x, p.y, 1.6, 0, 6.283); ctx.fill();
        for (var j = i + 1; j < P.length; j++) {
          var q = P[j], dx = p.x - q.x, dy = p.y - q.y, dd = dx * dx + dy * dy;
          if (dd < 16900) { ctx.strokeStyle = "rgba(125,170,255," + (.28 * (1 - dd / 16900)) + ")"; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); }
        }
        var ex = p.x - mx, ey = p.y - my, ed = ex * ex + ey * ey;
        if (ed < 22500) { ctx.strokeStyle = "rgba(139,92,246," + (.5 * (1 - ed / 22500)) + ")"; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(mx, my); ctx.stroke(); }
      }
      requestAnimationFrame(tick);
    };
    size(); window.addEventListener("resize", size);
    cv.parentNode.addEventListener("pointermove", function (e) { var r = cv.getBoundingClientRect(); mx = e.clientX - r.left; my = e.clientY - r.top; });
    new IntersectionObserver(function (en) { var v = en[0].isIntersecting; if (v && !run) { run = true; tick(); } else if (!v) run = false; }).observe(cv);
  }

  /* ---- 2) عدّادات KPI ---- */
  var fmt = function (v, dec, sep) { var s = v.toFixed(dec); return sep ? s.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : s; };
  Array.prototype.forEach.call(document.querySelectorAll("[data-count]"), function (el) {
    var to = parseFloat(el.dataset.count), dec = +el.dataset.dec || 0, suf = el.dataset.suf || "", sep = el.dataset.sep, t0 = null;
    if (reduce) { el.textContent = fmt(to, dec, sep) + suf; return; }
    (function step(t) {
      if (t0 === null) t0 = t; var k = Math.min((t - t0) / 1800, 1), e = 1 - Math.pow(1 - k, 3);
      el.textContent = fmt(to * e, dec, sep) + suf; if (k < 1) requestAnimationFrame(step);
    })(performance.now());
  });

  /* ---- 3) مخطط حيّ بتمرير مستمر ---- */
  var chL = $("chL"), chA = $("chA"), slide = $("slide");
  if (chL) {
    var N = 28, Wd = 400, step = Wd / (N - 1), v = 55, pts = [];
    var next = function () { v += (Math.random() - .45) * 18; v = Math.max(18, Math.min(88, v)); return v; };
    for (var i = 0; i <= N; i++) pts.push(next());
    var draw = function () {
      var d = "", i, y = function (a) { return 140 - a * 1.2 - 8; };
      for (i = 0; i < pts.length; i++) {
        var x = i * step;
        d += i ? " C" + (x - step / 2) + "," + y(pts[i - 1]) + " " + (x - step / 2) + "," + y(pts[i]) + " " + x + "," + y(pts[i]) : "M0," + y(pts[0]);
      }
      chL.setAttribute("d", d); chA.setAttribute("d", d + " L" + (pts.length - 1) * step + ",140 L0,140Z");
    };
    draw();
    if (!reduce) setInterval(function () {
      pts.shift(); pts.push(next()); draw();
      slide.style.transition = "none"; slide.style.transform = "translateX(" + step + "px)"; void slide.getBoundingClientRect();
      slide.style.transition = ""; slide.style.transform = "translateX(0)";
    }, 850);
  }

  /* ---- 4) أعمدة متحركة ---- */
  var bars = $("bars");
  if (bars) {
    for (var b = 0; b < 16; b++) bars.appendChild(document.createElement("i"));
    var set = function () { Array.prototype.forEach.call(bars.children, function (el) { el.style.height = 15 + Math.random() * 85 + "%"; }); };
    set(); if (!reduce) setInterval(set, 1400);
  }

  /* ---- 5) طرفية تكتب نفسها ---- */
  var term = $("term");
  if (term) {
    var L = ["$ betacode deploy --env production", "✓ build passed (214 tests)", "✓ sha256 verified", "✓ release v2.4.0 published", "→ 1,280 clients updated"], li = 0, ci = 0, text = "";
    if (reduce) { term.textContent = L.join("\n"); return; }
    (function type() {
      if (li >= L.length) { setTimeout(function () { li = 0; ci = 0; text = ""; term.textContent = ""; type(); }, 2600); return; }
      if (ci < L[li].length) { text += L[li][ci++]; term.textContent = text; setTimeout(type, 28 + Math.random() * 30); }
      else { text += "\n"; li++; ci = 0; term.textContent = text; setTimeout(type, 420); }
    })();
  }
})(); 
