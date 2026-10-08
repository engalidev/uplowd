/* سلوك مشترك للواجهة العامة */
(function () {
  "use strict";
  var d = document;
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }

  // قائمة الجوال
  var burger = d.getElementById("burger"), links = d.getElementById("links");
  if (burger && links) burger.addEventListener("click", function () { links.classList.toggle("open"); });

  // بحث وتصفية البرامج
  var search = d.getElementById("programSearch"), cards = $$(".pcard[data-name]"), none = d.getElementById("noResults"), cat = "";
  function filter() {
    var q = (search ? search.value : "").trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {
      var ok = (!q || c.dataset.name.indexOf(q) > -1) && (!cat || c.dataset.cat === cat);
      c.style.display = ok ? "" : "none"; if (ok) shown++;
    });
    if (none) none.style.display = shown ? "none" : "block";
  }
  if (search) search.addEventListener("input", filter);
  $$(".fchip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      $$(".fchip").forEach(function (c) { c.classList.remove("active"); });
      chip.classList.add("active"); cat = chip.dataset.filter || ""; filter();
    });
  });

  // نسخ النص
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var old = btn.textContent;
      (navigator.clipboard ? navigator.clipboard.writeText(btn.dataset.copy) : Promise.reject())
        .then(function () { btn.textContent = "تم النسخ ✓"; })
        .catch(function () { btn.textContent = "تعذر النسخ"; })
        .then(function () { setTimeout(function () { btn.textContent = old; }, 1600); });
    });
  });
})(); 
