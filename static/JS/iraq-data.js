/* بيانات المحافظات (حلبجة تظهر فقط إذا احتوى ملف GeoJSON عليها) — عدّل الأسماء والنصوص والرموز من هنا فقط.
   id يطابق المفتاح في iraq-map.js ، و icon يطابق مفتاحًا في IRAQ_ICONS. */
window.IRAQ_DATA = [
  { id: "duhok", alias: ["dahuk","dohuk","duhok","دهوك"],        ar: "دهوك",      en: "Duhok",        landmark: "معبد لالش",              icon: "cone",     desc: "جبال شاهقة وبوابات تاريخية وأقدم المعابد الإيزيدية." },
  { id: "nineveh", alias: ["ninawa","nineveh","ninewa","نينوى"],      ar: "نينوى",     en: "Nineveh",      landmark: "الثور المجنح الآشوري",   icon: "lamassu",  desc: "عاصمة الآشوريين ومدينة نمرود والحضر ومنارة الحدباء." },
  { id: "erbil", alias: ["arbil","erbil","irbil","hawler","أربيل","اربيل"],        ar: "أربيل",     en: "Erbil",        landmark: "قلعة أربيل",             icon: "citadel",  desc: "من أقدم المدن المأهولة في العالم بقلعتها فوق التل." },
  { id: "kirkuk", alias: ["kirkuk","tamim","attamim","كركوك","التأميم"],       ar: "كركوك",     en: "Kirkuk",       landmark: "نار بابا كركر",          icon: "flame",    desc: "مدينة القلعة القديمة وأولى حقول النفط في العراق." },
  { id: "sulaymaniyah", alias: ["sulaymaniyah","sulaimaniyah","sulaymaniya","slemani","السليمانية"], ar: "السليمانية",en: "Sulaymaniyah", landmark: "جبال أزمر وكويزة",       icon: "mountain", desc: "عاصمة الثقافة الكردية بجبالها وبحيراتها وشعرائها." },
  { id: "salahuddin", alias: ["salahaddin","salahuddin","saladin","salahaldin","salahdin","صلاحالدين","صلاح الدين"],   ar: "صلاح الدين",en: "Salah al-Din", landmark: "المئذنة الملوية - سامراء",icon: "spiral",   desc: "تكريت وسامراء، عاصمة العباسيين وملويتها الشهيرة." },
  { id: "diyala", alias: ["diyala","diala","ديالى"],       ar: "ديالى",     en: "Diyala",       landmark: "بساتين البرتقال",        icon: "orchard",  desc: "مدينة البساتين والحمضيات على ضفاف نهر ديالى." },
  { id: "anbar", alias: ["anbar","alanbar","الأنبار","انبار","أنبار"],        ar: "الأنبار",   en: "Anbar",        landmark: "نواعير هيت",             icon: "wheel",    desc: "أكبر المحافظات مساحة، على ضفاف الفرات ونواعيره." },
  { id: "baghdad", alias: ["baghdad","bagdad","بغداد"],      ar: "بغداد",     en: "Baghdad",      landmark: "بغداد العباسية",         icon: "dome",     desc: "مدينة السلام وبيت الحكمة وعاصمة العراق عبر العصور." },
  { id: "babylon", alias: ["babylon","babil","babel","بابل"],      ar: "بابل",      en: "Babylon",      landmark: "بوابة عشتار",            icon: "gate",     desc: "الحدائق المعلقة وشريعة حمورابي وحضارة وادي الرافدين." },
  { id: "karbala", alias: ["karbala","kerbala","karbalaa","كربلاء"],      ar: "كربلاء",    en: "Karbala",      landmark: "المرقدان الشريفان",      icon: "twin",     desc: "مدينة مقدسة بقبابها ومنائرها وزوّارها من كل العالم." },
  { id: "wasit", alias: ["wasit","wasat","واسط"],        ar: "واسط",      en: "Wasit",        landmark: "سدة الكوت",              icon: "barrage",  desc: "مدينة الكوت على دجلة وآثار مدينة واسط التاريخية." },
  { id: "najaf", alias: ["najaf","annajaf","النجف","نجف"],        ar: "النجف",     en: "Najaf",        landmark: "القبة الذهبية",          icon: "shrine",   desc: "عاصمة العلم الديني ومقبرة وادي السلام الشهيرة." },
  { id: "qadisiyyah", alias: ["qadisiyah","qadisiyyah","qadissiya","qadisiya","diwaniyah","القادسية","قادسية","الديوانية"],   ar: "القادسية",  en: "Al-Qadisiyyah",landmark: "سنابل الشلب",            icon: "wheat",    desc: "أرض معركة القادسية وسلة العراق من الرز والحنطة." },
  { id: "maysan", alias: ["maysan","misan","missan","ميسان"],       ar: "ميسان",     en: "Maysan",       landmark: "الأهوار والمشحوف",       icon: "marsh",    desc: "أهوار الجنوب المدرجة على لائحة التراث العالمي." },
  { id: "muthanna", alias: ["muthanna","muthana","المثنى","مثنى"],     ar: "المثنى",    en: "Muthanna",     landmark: "صحراء السماوة وأوروك",   icon: "dunes",    desc: "بادية واسعة وبوابة أوروك، أولى مدن التاريخ." },
  { id: "dhiqar", alias: ["dhiqar","thiqar","dhiqar","ذيقار","ذي قار"],       ar: "ذي قار",    en: "Dhi Qar",      landmark: "زقورة أور",              icon: "ziggurat", desc: "موطن أور السومرية ومهد النبي إبراهيم عليه السلام." },
  { id: "halabja", alias: ["halabja","halabjah","حلبجة"], ar: "حلبجة", en: "Halabja", landmark: "جبال هورامان", icon: "mountain", desc: "مدينة السلام والذاكرة، بين جبال هورامان وسهل شهرزور." },
  { id: "basra", alias: ["basra","basrah","albasrah","البصرة","بصرة"],        ar: "البصرة",    en: "Basra",        landmark: "النخيل وشط العرب",       icon: "palm",     desc: "ثغر العراق الباسم، ميناء ونفط ونخيل وسندباد." }
];

/* رموز بمقياس 64×64 (خطوط فقط) */
window.IRAQ_ICONS = {
  ziggurat: '<path d="M8 54h48M14 54V44h36v10M20 44V34h24v10M26 34V24h12v10M32 54V24M32 24v-6"/>',
  gate:     '<path d="M10 56V22h44v34M10 22l4-6h36l4 6M22 56V38a10 10 0 0 1 20 0v18M18 28h4M28 28h8M42 28h4"/>',
  lamassu:  '<path d="M14 56V28c0-10 8-18 18-18s18 8 18 18v28M24 56V42h16v14M20 28c4-6 20-6 24 0M26 32h12"/><circle cx="32" cy="22" r="3"/>',
  citadel:  '<path d="M8 56h48M14 56l-2-14h40l-2 14M16 42V28h32v14M16 28l2-4h4l2 4M26 28l2-4h4l2 4M36 28l2-4h4l2 4M28 56V48a4 4 0 0 1 8 0v8"/>',
  flame:    '<path d="M32 8c4 10 14 16 14 30a14 14 0 0 1-28 0c0-8 4-12 8-16 0 6 2 8 4 8 0-8-2-14 2-22zM32 56v-6"/>',
  mountain: '<path d="M6 54L22 28l10 14 8-10 18 22zM40 32l4 6"/>',
  spiral:   '<path d="M22 56h20M32 56V10M24 48c10-3 14-6 16-10M26 38c8-2 10-5 12-8M28 29c6-1 7-4 8-6M30 10l2-4 2 4"/>',
  orchard:  '<circle cx="32" cy="24" r="14"/><path d="M32 38v18M22 56h20"/><circle cx="27" cy="22" r="2"/><circle cx="37" cy="20" r="2"/><circle cx="33" cy="30" r="2"/>',
  wheel:    '<circle cx="32" cy="30" r="20"/><circle cx="32" cy="30" r="3"/><path d="M32 10v40M12 30h40M18 16l28 28M46 16L18 44M10 58h44"/>',
  dome:     '<path d="M10 56h44M14 56V36h36v20M16 36c0-10 7-16 16-16s16 6 16 16M32 20v-8M28 56V46a4 4 0 0 1 8 0v10"/>',
  twin:     '<path d="M8 56h48M14 56V16M50 56V16M10 24h8M46 24h8M12 16h4M48 16h4M22 56V44c0-6 4-10 10-10s10 4 10 10v12M32 34v-4"/>',
  barrage:  '<path d="M6 26h52M6 56h52M10 26v30M24 26v30M40 26v30M54 26v30M10 40a7 7 0 0 1 14 0M24 40a8 8 0 0 1 16 0M40 40a7 7 0 0 1 14 0M6 18h52"/>',
  shrine:   '<path d="M8 56h48M18 56V38a14 14 0 0 1 28 0v18M32 24v-10M30 14h4M12 56V28M52 56V28M10 28h4M50 28h4"/>',
  wheat:    '<path d="M32 58V14M32 22c-8 0-10-6-10-10 8 0 10 4 10 10M32 22c8 0 10-6 10-10-8 0-10 4-10 10M32 34c-8 0-10-6-10-10M32 34c8 0 10-6 10-10M32 46c-8 0-10-6-10-10M32 46c8 0 10-6 10-10"/>',
  marsh:    '<path d="M8 50c8 6 40 6 48 0l-4-6H12zM18 44V18M26 44V10M34 44V20M42 44V12"/>',
  dunes:    '<path d="M6 50c8-12 14-12 22 0 8-12 14-12 22 0M6 58h52"/><circle cx="44" cy="16" r="6"/>',
  palm:     '<path d="M32 58V28M32 28c-6-8-16-8-22-4 6 0 12 2 22 4zM32 28c6-8 16-8 22-4-6 0-12 2-22 4zM32 28c-2-8-8-14-14-14 6 2 10 8 14 14zM32 28c2-8 8-14 14-14-6 2-10 8-14 14zM32 28V12M10 58h44"/>',
  cone:     '<path d="M32 8l10 40H22zM26 48h12M28 36h8M30 24h4M14 56h36"/>'
};
