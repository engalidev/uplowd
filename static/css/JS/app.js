(function () {
  "use strict";
  var d = document, root = d.documentElement;
  function $(s, c) { return (c || d).querySelector(s); }
  function $$(s, c) { return Array.prototype.slice.call((c || d).querySelectorAll(s)); }

  // الوضع الداكن
  var themeBtn = $("#themeBtn");
  if (themeBtn) themeBtn.addEventListener("click", function () {
    var t = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = t;
    try { localStorage.setItem("theme", t); } catch (e) {}
  });

  // الشريط الجانبي على الجوال
  var sb = $("#sidebar"), scrim = $("#scrim"), mb = $("#menuBtn");
  function toggle(open) {
    if (!sb) return;
    sb.classList.toggle("open", open);
    if (scrim) scrim.classList.toggle("show", open);
  }
  if (mb) mb.addEventListener("click", function () { toggle(!sb.classList.contains("open")); });
  if (scrim) scrim.addEventListener("click", function () { toggle(false); });

  // إخفاء رسائل النجاح تلقائيًا
  $$(".flash.success").forEach(function (el) {
    setTimeout(function () { el.style.display = "none"; }, 6000);
  });

  // البحث والتصفية في صفحة البرامج
  var search = $("#programSearch"), cards = $$(".pcard[data-name]"), none = $("#noResults");
  var activeCat = "";
  function applyFilter() {
    var q = (search ? search.value : "").trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {
      var ok = (!q || c.dataset.name.indexOf(q) > -1) && (!activeCat || c.dataset.cat === activeCat);
      c.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    if (none) none.style.display = shown ? "none" : "block";
  }
  if (search) search.addEventListener("input", applyFilter);
  $$(".fchip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      $$(".fchip").forEach(function (c) { c.classList.remove("active"); });
      chip.classList.add("active");
      activeCat = chip.dataset.filter || "";
      applyFilter();
    });
  });

  // نسخ النص
  $$("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var old = btn.textContent;
      (navigator.clipboard ? navigator.clipboard.writeText(btn.dataset.copy) : Promise.reject())
        .then(function () { btn.textContent = "تم النسخ"; })
        .catch(function () { btn.textContent = "تعذر النسخ"; })
        .then(function () { setTimeout(function () { btn.textContent = old; }, 1600); });
    });
  });

  // النوافذ المنبثقة
  $$("[data-open]").forEach(function (b) {
    b.addEventListener("click", function () {
      var dlg = d.getElementById(b.dataset.open);
      if (dlg && dlg.showModal) dlg.showModal();
    });
  });
  $$("[data-close]").forEach(function (b) {
    b.addEventListener("click", function () { var dlg = b.closest("dialog"); if (dlg) dlg.close(); });
  });

  // تأكيد الحذف
  $$("form[data-confirm]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!confirm(f.dataset.confirm)) e.preventDefault();
    });
  });

  // اسم الملف المختار
  $$(".drop input[type=file]").forEach(function (inp) {
    inp.addEventListener("change", function () {
      var box = inp.closest(".drop"), label = $(".file-name", box), f = inp.files && inp.files[0];
      if (!f) { box.classList.remove("has"); return; }
      box.classList.add("has");
      label.textContent = f.name + " — " + (f.size / 1048576).toFixed(1) + " MB";
    });
  });

  // الرفع مع شريط تقدم
  $$("form[data-upload]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var file = $("input[type=file]", form), err = $(".form-error", form);
      var prog = $(".progress", form), bar = $(".bar i", form), pct = $(".pct", form), size = $(".sz", form);
      var btn = $("button[type=submit]", form);
      e.preventDefault();
      err.style.display = "none";
      if (!file.files.length) { err.textContent = "اختر ملف التحديث أولًا."; err.style.display = "block"; return; }
      if (!confirm("هل تريد نشر الإصدار " + $("[name=version]", form).value.trim() + " الآن؟")) return;

      var xhr = new XMLHttpRequest();
      xhr.open("POST", form.action);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      btn.disabled = true;
      prog.classList.add("show");
      xhr.upload.onprogress = function (ev) {
        if (!ev.lengthComputable) return;
        var p = Math.round(ev.loaded / ev.total * 100);
        bar.style.width = p + "%";
        pct.textContent = p + "%";
        size.textContent = (ev.loaded / 1048576).toFixed(1) + " / " + (ev.total / 1048576).toFixed(1) + " MB";
        if (p === 100) pct.textContent = "جارٍ المعالجة والتحقق…";
      };
      xhr.onload = function () {
        try {
          var res = JSON.parse(xhr.responseText);
          if (xhr.status === 200 && res.redirect) { location.href = res.redirect; return; }
        } catch (x) {}
        fail(xhr.status === 413 ? "حجم الملف يتجاوز الحد المسموح." : "فشل الرفع. أعد تحميل الصفحة وحاول مرة أخرى.");
      };
      xhr.onerror = function () { fail("انقطع الاتصال أثناء الرفع. تحقق من الشبكة وأعد المحاولة."); };
      function fail(msg) {
        btn.disabled = false;
        prog.classList.remove("show");
        err.textContent = msg;
        err.style.display = "block";
      }
      xhr.send(new FormData(form));
    });
  });
})();
