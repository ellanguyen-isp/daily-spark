// Community users: change SITE to your own daily-spark GitHub Pages address.
var SITE = "https://ellanguyen-isp.github.io/daily-spark/";

var MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var MARK = '<svg viewBox="320 320 614 614" aria-hidden="true" fill="currentColor"><polygon points="625,332 638,332 657,535 607,557"/><polygon points="607,712 660,688 638,920 626,920"/><polygon points="333,613 632,590 920,613 920,628 646,650 333,628"/><polygon points="371,767 547,645 632,590 881,473 889,487 727,598 646,651 378,780"/></svg>';
var T = {
  en: { full: "Read the full spark →", fullw: "Read this week →", edition: "Edition", weekly: "Weekly", frontier: "Frontier", people: "People", shift: "This week", mega: "Mega trend", hype: "Hype", radar: "Radar",
        fail: "Could not load today's spark. Check your connection, or open the site.", hint: "Open a stamp to read. Read stamps turn blue." },
  vi: { full: "Đọc spark đầy đủ →", fullw: "Đọc bản tuần này →", edition: "Số", weekly: "Hằng tuần", frontier: "Tin nóng", people: "Người theo dõi", shift: "Tuần này", mega: "Xu hướng lớn", hype: "Cơn sốt", radar: "Radar",
        fail: "Không tải được spark hôm nay. Kiểm tra kết nối, hoặc mở trang web.", hint: "Mở một con tem để đọc. Tem đã đọc sẽ chuyển màu xanh." }
};
var lang = get("ds-nt-lang", "en");
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

// stable "random" tilt and offset per stamp, so the poster does not jump on every new tab
var TILT = [-2, 1.5, -1, 2, -1.5, 1, -1.8, 0.8];
var DROP = ["0px", "8px", "-4px", "10px", "2px", "-6px", "6px", "-2px"];
var SIZE = ["", "wide", "", "", "wide", "", "", "wide"];

function render() {
  var t = T[lang], field = document.getElementById("field");
  document.documentElement.lang = lang;
  document.getElementById("mark").innerHTML = MARK;
  document.getElementById("brand").href = SITE;
  field.textContent = "";
  if (!data) { field.appendChild(el("p", { class: "status" }, t.fail)); return; }
  var weekly = data.type === "weekly", link = SITE + "#" + data.date, seen = seenMap();
  document.body.className = weekly ? "weekly" : "daily";
  document.getElementById("date").textContent = fmt(data.date);
  document.getElementById("ed").textContent = weekly ? t.weekly + " · " + data.edition : t.edition + " " + data.edition;
  document.getElementById("headline").textContent = head(L(data.summary));
  var full = document.getElementById("full");
  full.href = link; full.textContent = weekly ? t.fullw : t.full;

  var list = data.stamps || (data.headlines || []).map(function (h) { return { t: h.t, src: h.src, url: h.url, kind: weekly ? "shift" : "frontier" }; });
  list.forEach(function (s, i) {
    var a = el("a", { class: "stamp " + SIZE[i % SIZE.length] + (seen[s.url] ? " seen" : ""), href: s.url, title: L(s.t),
      style: "--r:" + TILT[i % TILT.length] + "deg;--y:" + DROP[i % DROP.length] });
    var meta = el("span", { class: "meta" });
    meta.appendChild(el("span", {}, s.who || s.src || ""));
    meta.appendChild(el("span", {}, short(s.date)));
    a.appendChild(meta);
    a.appendChild(el("h2", {}, L(s.t)));
    var foot = el("span", { class: "foot" });
    foot.appendChild(el("span", {}, s.tag || t[s.kind] || ""));
    foot.appendChild(el("span", { class: "no" }, String(i + 1).padStart(2, "0")));
    a.appendChild(foot);
    a.addEventListener("click", function () { markSeen(s.url); a.classList.add("seen"); });
    a.addEventListener("auxclick", function () { markSeen(s.url); a.classList.add("seen"); });
    field.appendChild(a);
  });
  // balanced rows: 2 rows up to 10 stamps, then 3 rows
  var rows = list.length > 10 ? 3 : 2;
  field.style.maxWidth = list.length > 4 ? (Math.ceil(list.length / rows) * 280) + "px" : "";

  var seg = document.getElementById("seg");
  seg.textContent = "";
  ["en", "vi"].forEach(function (l) {
    var b = el("button", { type: "button", "aria-pressed": String(lang === l) }, l.toUpperCase());
    b.addEventListener("click", function () { lang = l; set("ds-nt-lang", l); render(); });
    seg.appendChild(b);
  });
}

fetch(SITE + "latest.json", { cache: "no-cache" })
  .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(function (d) { data = d; render(); })
  .catch(function () { data = null; render(); });
