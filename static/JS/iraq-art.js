/* رسومات المعالم (مقياس 120×100، خط الأرض y=96).
   الأنماط: بلا صنف = حجر، gd = ذهب، ln = خطوط، dk = فتحات، gr = خضرة، wt = ماء، sn = ثلج. */
(function () {
  function wheat() {
    var s = "";
    [[26, 62], [60, 74], [94, 56]].forEach(function (p) {
      var x = p[0], h = p[1], top = 96 - h, g = "";
      for (var i = 0; i < 5; i++) { var y = top + 4 + i * 11; g += "M0 " + y + "q-8 -3 -8 -12q8 3 8 12M0 " + y + "q8 -3 8 -12q-8 3 -8 12"; }
      s += '<g transform="translate(' + x + ' 0)"><g class="ln"><path d="M0 96V' + (top - 6) + '"/></g><g class="gd"><path d="' + g + 'M0 ' + top + 'q-4 -6 0 -14q4 8 0 14"/></g></g>';
    });
    return s;
  }
  window.IRAQ_ART = {
    pin: '<g><path d="M60 14a24 24 0 0 1 24 24c0 18-24 48-24 48S36 56 36 38a24 24 0 0 1 24-24Z"/></g><g class="gd"><circle cx="60" cy="38" r="9"/></g>',

    erbil: '<g><path d="M6 96C14 82 22 70 30 62H90C98 70 106 82 114 96Z"/><path d="M30 62V56H90V62"/></g><g class="ln"><path d="M18 84H102M25 73H95"/></g>' +
      '<g><path d="M34 56V46H44V56M46 56V38H58V56M60 56V44H70V56M72 56V36H82V56M84 56V47H90V56"/></g><g class="gd"><path d="M46 38l6-8 6 8zM72 36l5-7 5 7z"/></g><g class="dk"><path d="M52 96V86a8 8 0 0 1 16 0V96Z"/></g>',

    salahuddin: '<g><path d="M8 96V90H112V96"/><path d="M42 90V84H78V90"/><path d="M46 84L53 26H67L74 84Z"/><path d="M52 26H68V20H52Z"/></g>' +
      '<g class="ln"><path d="M47 78Q76 72 49 63Q73 57 51 48Q70 43 53 36Q66 31 55 27"/></g><g class="gd"><path d="M54 20a6 6 0 0 1 12 0ZM60 14V5"/></g>',

    najaf: '<g><path d="M24 96V72H96V96Z"/><path d="M42 72V64H78V72"/></g><g class="gd"><path d="M37 64C37 36 83 36 83 64Z"/><path d="M60 40V28"/><circle cx="60" cy="25" r="3.2"/>' +
      '<path d="M14 96V40H24V96ZM96 96V40H106V96Z"/><path d="M13 40a6 6 0 0 1 12 0ZM95 40a6 6 0 0 1 12 0Z"/></g><g class="dk"><path d="M50 96V84a10 10 0 0 1 20 0V96Z"/></g>',

    karbala: '<g><path d="M6 96V76H60V96Z"/><path d="M62 96V80H114V96Z"/></g>' +
      '<g class="gd"><path d="M16 76C16 46 50 46 50 76Z"/><path d="M33 49V39"/><circle cx="33" cy="36" r="3"/><path d="M76 80C76 58 108 58 108 80Z"/><path d="M92 60V52"/><circle cx="92" cy="49" r="3"/>' +
      '<path d="M4 96V38H9V96ZM52 96V38H57V96ZM66 96V44H71V96ZM110 96V44H115V96Z"/><path d="M3 38a3.5 3.5 0 0 1 7 0ZM51 38a3.5 3.5 0 0 1 7 0ZM65 44a3.5 3.5 0 0 1 7 0ZM109 44a3.5 3.5 0 0 1 7 0Z"/></g>' +
      '<g class="dk"><path d="M24 96V86a7 7 0 0 1 14 0V96ZM84 96V90a6 6 0 0 1 12 0V96Z"/></g>',

    nineveh: '<g><path d="M14 60C14 48 24 44 38 44H80C90 44 96 50 96 58V96H88V74H80V96H72V80H46V96H38V74H30V96H22V68C16 68 14 64 14 60Z"/></g>' +
      '<g class="gd"><path d="M74 46C70 30 52 18 28 14C32 20 34 24 36 28C28 24 24 24 20 24C26 30 30 34 34 40C28 38 26 40 22 40C30 46 40 48 52 48Z"/></g>' +
      '<g class="ln"><path d="M40 30L62 46M34 36L56 47M52 24L68 44M26 32L46 45M96 38Q102 56 108 38M4 62Q-2 52 6 49"/></g>' +
      '<g><circle cx="102" cy="34" r="9"/><path d="M94 42V52H110V42"/></g><g class="gd"><path d="M92 28H112V22H92ZM94 22V14H110V22Z"/></g>',

    babylon: '<g><path d="M10 96V22H40V40H80V22H110V96Z"/></g><g class="dk"><path d="M48 96V70a12 12 0 0 1 24 0V96Z"/></g>' +
      '<g class="ln"><path d="M10 22v-5h6v5M20 22v-5h6v5M30 22v-5h6v5M84 22v-5h6v5M94 22v-5h6v5M104 22v-5h6v5M10 32H40M80 32H110M10 44H40M80 44H110M10 56H40M80 56H110M10 70H40M80 70H110M44 54H76"/></g>' +
      '<g class="gd"><path d="M16 50h6v5h-6zM28 50h6v5h-6zM16 62h6v5h-6zM28 62h6v5h-6zM86 50h6v5h-6zM98 50h6v5h-6zM86 62h6v5h-6zM98 62h6v5h-6zM16 78h6v5h-6zM28 78h6v5h-6zM86 78h6v5h-6zM98 78h6v5h-6z"/></g>',

    dhiqar: '<g><path d="M6 96L16 68H104L114 96Z"/><path d="M24 68L30 50H90L96 68Z"/><path d="M38 50L42 36H78L82 50Z"/><path d="M52 36V26H68V36Z"/></g>' +
      '<g class="ln"><path d="M52 96L56 68H64L68 96M56 68L58 50H62L64 68M58 50L59 36H61L62 50M52 86H68M54 77H66"/></g><g class="dk"><path d="M57 34V28H63V34Z"/></g>',

    basra: '<g class="ln"><path d="M32 96C29 76 33 56 36 40M94 96C92 80 95 64 97 52"/></g>' +
      '<g class="gr"><path d="M36 40C24 32 12 34 4 44C16 40 26 40 36 40ZM36 40C26 26 16 24 8 26C20 28 28 32 36 40ZM36 40C36 26 34 16 30 8C28 22 30 30 36 40ZM36 40C46 28 58 26 66 30C54 32 46 34 36 40ZM36 40C48 38 58 44 62 54C52 46 44 44 36 40Z"/>' +
      '<path d="M97 52C87 46 77 48 71 56C81 52 89 52 97 52ZM97 52C89 42 79 40 73 42C83 44 91 46 97 52ZM97 52C99 42 98 34 95 28C92 38 94 46 97 52ZM97 52C106 44 114 44 118 50C110 50 104 50 97 52ZM97 52C104 54 112 60 114 68C108 60 102 56 97 52Z"/></g>' +
      '<g><path d="M46 88H82L76 96H52Z"/><path d="M64 88V54L86 84H64Z"/></g><g class="wt"><path d="M0 94Q8 90 16 94T32 94T48 94T64 94T80 94T96 94T112 94T120 94"/></g>',

    baghdad: '<g><path d="M26 96V34H94V96Z"/><path d="M26 34V28H34V34M40 34V28H48V34M54 34V28H62V34M68 34V28H76V34M82 34V28H90V34"/></g>' +
      '<g class="gd"><path d="M42 28C42 8 78 8 78 28Z"/><path d="M60 12V4"/></g><g class="dk"><path d="M46 96V66Q60 36 74 66V96Z"/></g>' +
      '<g class="ln"><path d="M26 44H94M26 52H94M34 44V52M46 44V52M58 44V52M70 44V52M82 44V52M52 96V70Q60 50 68 70V96"/></g>',

    diyala: '<g class="ln"><path d="M60 96V66M30 96H90"/></g><g class="gr"><path d="M28 62C16 40 34 20 60 22C86 20 104 40 92 62C86 72 34 72 28 62Z"/></g>' +
      '<g class="gd"><circle cx="44" cy="44" r="5"/><circle cx="68" cy="36" r="5"/><circle cx="80" cy="54" r="5"/><circle cx="54" cy="58" r="5"/><circle cx="70" cy="64" r="5"/><circle cx="38" cy="58" r="5"/></g>',

    anbar: '<g><path d="M40 52L33 96H59L52 52Z"/></g><g class="ln"><path d="M12 52H80M16.6 35L75.4 69M29 22.6L63 81.4M46 18V86M63 22.6L29 81.4M75.4 35L16.6 69"/></g>' +
      '<g><circle cx="46" cy="52" r="34"/><circle cx="46" cy="52" r="26"/><circle cx="46" cy="52" r="5"/></g>' +
      '<g class="gd"><circle cx="80" cy="52" r="2.8"/><circle cx="75.4" cy="35" r="2.8"/><circle cx="63" cy="22.6" r="2.8"/><circle cx="46" cy="18" r="2.8"/><circle cx="29" cy="22.6" r="2.8"/><circle cx="16.6" cy="35" r="2.8"/><circle cx="12" cy="52" r="2.8"/><circle cx="16.6" cy="69" r="2.8"/><circle cx="29" cy="81.4" r="2.8"/><circle cx="46" cy="86" r="2.8"/><circle cx="63" cy="81.4" r="2.8"/><circle cx="75.4" cy="69" r="2.8"/></g>' +
      '<g><path d="M86 56H118V96H86Z"/></g><g class="ln"><path d="M90 96V80a5 5 0 0 1 10 0V96M104 96V80a5 5 0 0 1 10 0V96"/></g><g class="wt"><path d="M86 56H118"/></g>' +
      '<g class="wf"><path d="M0 80Q10 76 20 80T40 80T60 80T80 80T100 80T120 80V96H0Z"/></g>',

    wasit: '<g><path d="M2 40H118V50H2Z"/><path d="M2 40V22H16V40M104 40V22H118V40"/></g><g class="ln"><path d="M10 50V96M32 50V96M54 50V96M76 50V96M98 50V96"/></g>' +
      '<g class="dk"><path d="M12 96V72a9 9 0 0 1 18 0V96ZM34 96V72a9 9 0 0 1 18 0V96ZM56 96V72a9 9 0 0 1 18 0V96ZM78 96V72a9 9 0 0 1 18 0V96Z"/></g><g class="wt"><path d="M0 92Q8 88 16 92T32 92T48 92T64 92T80 92T96 92T112 92T120 92"/></g>',

    qadisiyyah: wheat(),

    maysan: '<g class="ln"><path d="M5 96V52M10 96V44M15 96V58M105 96V54M110 96V44M115 96V56"/></g><g><path d="M22 96V68C22 36 40 24 60 24S98 36 98 68V96Z"/></g>' +
      '<g class="ln"><path d="M32 96V66C32 44 44 34 60 34M44 96V64C44 46 52 38 60 36M76 96V64C76 46 68 38 60 36M88 96V66C88 44 76 34 60 34M22 60H98M26 46H94"/></g>' +
      '<g class="dk"><path d="M50 96V74Q60 62 70 74V96Z"/></g><g class="gd"><path d="M78 92Q98 100 120 88Q100 94 78 92Z"/></g><g class="wt"><path d="M0 95Q10 92 20 95T40 95T60 95T80 95T100 95T120 95"/></g>',

    muthanna: '<g><path d="M0 96C16 78 36 74 60 74C84 74 100 78 120 90V96Z"/></g><g><path d="M44 74L48 64H72L76 74Z"/><path d="M52 64V52H68V64Z"/></g>' +
      '<g class="dk"><path d="M57 64V56H63V64Z"/></g><g class="gd"><circle cx="98" cy="24" r="9"/></g><g class="ln"><path d="M10 90C30 84 50 88 70 94M72 90C90 84 100 86 116 90"/></g>',

    duhok: '<g><path d="M30 96V78H60V96ZM66 96V82H98V96Z"/><path d="M34 78L45 22L56 78Z"/><path d="M70 82L82 42L94 82Z"/></g>' +
      '<g class="ln"><path d="M45 22V78M45 22L39 78M45 22L51 78M82 42V82M82 42L76 82M82 42L88 82M4 96H116"/></g><g class="gd"><circle cx="45" cy="20" r="3.5"/><circle cx="82" cy="40" r="3.5"/></g>',

    kirkuk: '<g><path d="M44 96L56 22H68L80 96Z"/></g><g class="ln"><path d="M47 76H77M50 60H74M53 44H71M44 96L72 60M80 96L52 60M47 76L68 44M77 76L56 44M20 96V62"/></g>' +
      '<g class="gd"><path d="M20 62C8 48 24 42 20 24C34 38 38 52 28 62Z"/></g>',

    sulaymaniyah: '<g><path d="M0 96L34 40L52 66L72 30L120 96Z"/></g><g class="sn"><path d="M26 52L34 40L42 54L37 51L34 56L30 51Z"/><path d="M62 46L72 30L82 48L76 44L72 50L67 44Z"/></g>' +
      '<g class="ln"><path d="M34 40L30 96M72 30L68 96M72 30L88 96"/></g>'
  };
  window.IRAQ_ART.halabja = window.IRAQ_ART.sulaymaniyah;
})();
