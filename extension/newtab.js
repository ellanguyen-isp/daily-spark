// Community users: change SITE to your own daily-spark GitHub Pages address.
var SITE = "https://ellanguyen-isp.github.io/daily-spark/";

var MO = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var WD = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
var T = {
  en: { big: "The big picture", heads: "Today's frontier", q: "Today's question", full: "Read the full spark →", fail: "Could not load today's spark. Check your connection, or open the site." },
  vi: { big: "Bức tranh lớn", heads: "Tin nóng hôm nay", q: "Câu hỏi hôm nay", full: "Đọc spark đầy đủ →", fail: "Không tải được spark hôm nay. Kiểm tra kết nối, hoặc mở trang web." }
};
var lang = "en";
try { lang = localStorage.getItem("ds-nt-lang") || "en"; } catch (e) {}
var data = null;

function el(tag, attrs, text) {
  var n = document.createElement(tag);
  Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
  if (text != null) n.textContent = text;
  return n;
}
function L(o) { return o && typeof o === "object" ? (o[lang] || o.en) : o; }
function fmt(s) { var p = s.split("-"); var d = new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); return WD[d.getUTCDay()] + " " + d.getUTCDate() + " " + MO[d.getUTCMonth()] + " " + d.getUTCFullYear(); }

function render() {
  var card = document.getElementById("card");
  var t = T[lang];
  card.textContent = "";
  var head = el("div", { class: "head" });
  head.appendChild(el("span", { class: "wordmark" }, "daily-spark"));
  head.appendChild(el("span", { class: "lbl muted num" }, data ? fmt(data.date) : ""));
  card.appendChild(head);
  if (!data) { card.appendChild(el("p", { class: "small" }, t.fail)); return; }
  var link = SITE + "#" + data.date;

  var big = el("div", { class: "box" });
  big.appendChild(el("span", { class: "lbl" }, t.big));
  big.appendChild(el("p", {}, L(data.big)));
  card.appendChild(big);

  var hb = el("div", {});
  hb.appendChild(el("span", { class: "lbl" }, t.heads));
  var ul = el("ul", { class: "heads" });
  data.headlines.forEach(function (h) {
    var li = el("li"), a = el("a", { href: h.url, target: "_blank", rel: "noopener" });
    a.appendChild(el("span", {}, L(h.t)));
    a.appendChild(el("span", { class: "src" }, h.src || ""));
    li.appendChild(a); ul.appendChild(li);
  });
  hb.appendChild(ul);
  card.appendChild(hb);

  var q = el("div", { class: "box" });
  q.appendChild(el("span", { class: "lbl" }, t.q));
  q.appendChild(el("p", {}, L(data.question)));
  card.appendChild(q);

  var btns = el("div", { class: "btns" });
  data.exercises.forEach(function (e) { btns.appendChild(el("a", { href: link, title: L(e.g) }, L(e.tag) + " · " + e.time)); });
  card.appendChild(btns);

  var foot = el("div", { class: "foot" });
  foot.appendChild(el("a", { class: "readfull", href: link }, t.full));
  var seg = el("div", { class: "seg", role: "group", "aria-label": "Language" });
  ["en", "vi"].forEach(function (l) {
    var b = el("button", { type: "button", "aria-pressed": String(lang === l) }, l.toUpperCase());
    b.addEventListener("click", function () { lang = l; try { localStorage.setItem("ds-nt-lang", l); } catch (e) {} render(); });
    seg.appendChild(b);
  });
  foot.appendChild(seg);
  card.appendChild(foot);
}

fetch(SITE + "latest.json", { cache: "no-cache" })
  .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
  .then(function (d) { data = d; render(); })
  .catch(function () { data = null; render(); });
