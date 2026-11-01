// The new tab page lives at <site>/newtab/, so the site address is one folder up.
var SITE = new URL("../", location.href).href;

var MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var MARK = '<svg viewBox="320 320 614 614" aria-hidden="true" fill="currentColor"><polygon points="625,332 638,332 657,535 607,557"/><polygon points="607,712 660,688 638,920 626,920"/><polygon points="333,613 632,590 920,613 920,628 646,650 333,628"/><polygon points="371,767 547,645 632,590 881,473 889,487 727,598 646,651 378,780"/></svg>';
var T = {
  en: { home: "Open daily spark", full: "Read this spark", fullw: "Read this week", edition: "Edition", weekly: "Weekly", frontier: "Frontier", people: "People", shift: "This week", mega: "Mega trend", hype: "Hype", radar: "Radar",
        fail: "Could not load today's spark. Check your connection, or open the site.", hint: "Open a stamp to read. Read stamps turn blue.", read: "read" },
  vi: { home: "Mở daily spark", full: "Đọc spark này", fullw: "Đọc bản tuần này", edition: "Số", weekly: "Hằng tuần", frontier: "Tin nóng", people: "Người theo dõi", shift: "Tuần này", mega: "Xu hướng lớn", hype: "Cơn sốt", radar: "Radar",
        fail: "Không tải được spark hôm nay. Kiểm tra kết nối, hoặc mở trang web.", hint: "Mở một con tem để đọc. Tem đã đọc sẽ chuyển màu xanh.", read: "đã đọc" }
};
// language follows the site's Menu > Language setting
var lang = (function () { try { return JSON.parse(get("ds-lang", '"en"')) === "vi" ? "vi" : "en"; } catch (e) { return "en"; } })();
var ARROW = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';
var data = null;

function get(k, d) { try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } }
function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
function seenMap() { try { return JSON.parse(get("ds-nt-seen", "{}")) || {}; } catch (e) { return {}; } }
function markSeen(url) { var m = seenMap(); m[url] = Date.now(); var keys = Object.keys(m); if (keys.length > 300) keys.slice(0, keys.length - 300).forEach(function (k) { delete m[k]; }); set("ds-nt-seen", JSON.stringify(m)); }
function el(tag, attrs, text) {
  var n = document.createElement(tag);
  Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
  if (text != null) n.textContent = text;
  return n;
}
function L(o) { return o && typeof o === "object" ? (o[lang] || o.en) : (o || ""); }
function pd(s) { var p = s.split("-"); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
function fmt(s) { var d = pd(s); return WD[d.getUTCDay()] + " " + d.getUTCDate() + " " + MO[d.getUTCMonth()] + " " + d.getUTCFullYear(); }
function short(s) { if (!/^\d{4}-\d{2}-\d{2}$/.test(s || "")) return ""; var d = pd(s); return d.getUTCDate() + " " + MO[d.getUTCMonth()]; }
function head(t) { var i = t.indexOf(": "); return i > 0 ? t.slice(0, i) : t; }

// Equal stamps in balanced rows: 1 row up to 5, 2 rows up to 12, then 3. The last row is centered.
var GAP = 24;
function layout() {
  var field = document.getElementById("field"), cards = field.querySelectorAll(".stamp"), n = cards.length;
  if (!n) return;
  var avail = field.clientWidth || window.innerWidth - 64, phone = window.innerWidth < 760;
  var rows = phone ? Math.ceil(n / 2) : n <= 5 ? 1 : n <= 12 ? 2 : 3, cols = Math.ceil(n / rows);
  var w = Math.max(140, Math.min(232, Math.floor((avail - (cols - 1) * GAP) / cols)));
  field.style.maxWidth = (cols * w + (cols - 1) * GAP) + "px";
  var tallest = 0;
  cards.forEach(function (c) { c.style.setProperty("--w", w + "px"); c.firstChild.style.minHeight = ""; });
  cards.forEach(function (c) { tallest = Math.max(tallest, c.firstChild.getBoundingClientRect().height); });
  cards.forEach(function (c) { c.firstChild.style.minHeight = tallest + "px"; });
}
window.addEventListener("resize", layout);

function render() {
  var t = T[lang], field = document.getElementById("field");
  document.documentElement.lang = lang;
  document.getElementById("mark").innerHTML = MARK;
  document.getElementById("brand").href = SITE;
  var home = document.getElementById("home"); home.href = SITE; home.textContent = t.home;
  field.textContent = "";
  if (!data) { field.appendChild(el("p", { class: "status" }, t.fail)); return; }
  var weekly = data.type === "weekly", link = SITE + "#" + data.date, seen = seenMap();
  document.getElementById("date").textContent = fmt(data.date);
  document.getElementById("ed").textContent = weekly ? t.weekly + " · " + data.edition : t.edition + " " + data.edition;
  document.getElementById("headline").textContent = head(L(data.summary));
  var full = document.getElementById("full");
  full.href = link; full.innerHTML = ""; full.appendChild(document.createTextNode(weekly ? t.fullw : t.full)); full.insertAdjacentHTML("beforeend", ARROW);
  var read = 0;

  var list = data.stamps || (data.headlines || []).map(function (h) { return { t: h.t, src: h.src, url: h.url, kind: weekly ? "shift" : "frontier" }; });
  list.forEach(function (s, i) {
    if (seen[s.url]) read++;
    var a = el("a", { class: "stamp" + (seen[s.url] ? " seen" : ""), href: s.url, title: L(s.t) });
    var inner = el("span", { class: "in" });
    var meta = el("span", { class: "meta" });
    meta.appendChild(el("span", {}, s.who || s.src || ""));
    meta.appendChild(el("span", {}, short(s.date)));
    inner.appendChild(meta);
    inner.appendChild(el("h2", {}, L(s.t)));
    var foot = el("span", { class: "foot" });
    foot.appendChild(el("span", {}, s.tag || t[s.kind] || ""));
    foot.appendChild(el("span", { class: "no" }, String(i + 1).padStart(2, "0")));
    inner.appendChild(foot);
    a.appendChild(inner);
    a.addEventListener("click", function () { markSeen(s.url); a.classList.add("seen"); });
    a.addEventListener("auxclick", function () { markSeen(s.url); a.classList.add("seen"); });
    field.appendChild(a);
  });
  document.getElementById("ed").textContent += " · " + read + " / " + list.length + " " + t.read;
  layout();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
}

// Google apps panel: plain links with simple generic icons (edit APPS to choose your own).
var IC = {
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
  drive: '<path d="M8 3h8l6 10-4 7H6l-4-7z"/><path d="M8 3l6 10h8M2 13h12l-4 7"/>',
  spark: '<path d="M12 2c.6 5 4.9 9.4 10 10-5.1.6-9.4 5-10 10-.6-5-4.9-9.4-10-10 5.1-.6 9.4-5 10-10z"/>',
  doc: '<path d="M6 2h8l5 5v15H6z"/><path d="M14 2v5h5M9 13h7M9 17h5"/>',
  sheet: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M9 4v16"/>',
  slide: '<rect x="3" y="5" width="18" height="14" rx="2"/><rect x="7" y="9" width="10" height="6" rx="1"/>',
  cal: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  chat: '<path d="M4 5h16v11H9l-5 4z"/>',
  video: '<rect x="2" y="6" width="13" height="12" rx="2"/><path d="M15 10l7-4v12l-7-4"/>',
  keep: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.7.7 1 1.5 1 2.5h6c0-1 .3-1.8 1-2.5A6 6 0 0 0 12 3z"/>',
  photo: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  map: '<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
  yt: '<rect x="2" y="5" width="20" height="14" rx="4"/><path d="M10 9l5 3-5 3z"/>',
  tr: '<path d="M4 5h9M8.5 3v2M6 5c0 4 3 7 6 8M11 5c0 3-3 7-7 9M13 21l4-10 4 10M14.5 17h5"/>'
};
var APPS = [
  ["Account", "https://myaccount.google.com/", "user", "#6a5acd"], ["Gmail", "https://mail.google.com/mail/", "mail", "#d93025"], ["Drive", "https://drive.google.com/", "drive", "#1e8e3e"],
  ["Gemini", "https://gemini.google.com/", "spark", "#5b6ee1"], ["Docs", "https://docs.google.com/document/", "doc", "#4285f4"], ["Sheets", "https://docs.google.com/spreadsheets/", "sheet", "#188038"],
  ["Slides", "https://docs.google.com/presentation/", "slide", "#f2a600"], ["Calendar", "https://calendar.google.com/", "cal", "#1a73e8"], ["Chat", "https://chat.google.com/", "chat", "#34a853"]
];
var MORE = [
  ["Meet", "https://meet.google.com/", "video", "#00897b"], ["Keep", "https://keep.google.com/", "keep", "#f9ab00"], ["Photos", "https://photos.google.com/", "photo", "#ea4335"],
  ["Maps", "https://maps.google.com/", "map", "#34a853"], ["YouTube", "https://www.youtube.com/", "yt", "#e53935"], ["Translate", "https://translate.google.com/", "tr", "#4285f4"]
];
function appLinks(list) {
  return list.map(function (a) {
    return '<a href="' + a[1] + '"><span class="ic" style="background:' + a[3] + '"><svg viewBox="0 0 24 24" aria-hidden="true">' + IC[a[2]] + '</svg></span><span>' + a[0] + '</span></a>';
  }).join("");
}
(function () {
  var btn = document.getElementById("appsBtn"), panel = document.getElementById("appsPanel");
  panel.innerHTML = '<div class="fav"><h3>Your favorites</h3><div class="grid">' + appLinks(APPS) + '</div></div><div class="grid more">' + appLinks(MORE) + '</div>';
  function show(on) { panel.hidden = !on; btn.setAttribute("aria-expanded", String(on)); }
  btn.addEventListener("click", function (e) { e.stopPropagation(); show(panel.hidden); });
  document.addEventListener("click", function (e) { if (!panel.hidden && !panel.contains(e.target)) show(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") show(false); });
})();

fetch(SITE + "latest.json", { cache: "no-cache" })
  .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(function (d) { data = d; render(); })
  .catch(function () { data = null; render(); });
