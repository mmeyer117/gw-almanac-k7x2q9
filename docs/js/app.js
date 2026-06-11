/* The Gateway Almanac — vanilla SPA: Today / Archive / Stats.
   Data: data/index.json + data/reports/YYYY-MM-DD.json (static, committed daily). */
(function () {
  "use strict";

  var $view = document.getElementById("view");
  var $flap = document.getElementById("flap-date");
  var $dayNav = document.getElementById("day-nav");
  var $prevBtn = document.getElementById("prev-day");
  var $nextBtn = document.getElementById("next-day");

  var state = {
    index: null,
    dates: [],          // ascending
    reports: {},        // date -> report
    current: null,      // date shown in day view
    chartsReady: false,
    charts: [],         // live Chart instances to destroy on view change
  };

  /* ---------------- utils ---------------- */

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fetchJSON(url) {
    return fetch(url, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error(url + " -> " + r.status);
      return r.json();
    });
  }

  function getReport(date) {
    if (state.reports[date]) return Promise.resolve(state.reports[date]);
    return fetchJSON("data/reports/" + date + ".json").then(function (rep) {
      state.reports[date] = rep;
      return rep;
    });
  }

  function getAllReports() {
    return Promise.all(state.dates.map(function (d) {
      return getReport(d).catch(function () { return null; });
    })).then(function (list) { return list.filter(Boolean); });
  }

  function parseDate(s) {
    var p = s.split("-");
    return new Date(+p[0], +p[1] - 1, +p[2]);
  }

  var MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
  var DOWS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

  function flapDate(dateStr) {
    var d = parseDate(dateStr);
    window.flapSet($flap, DOWS[d.getDay()] + " " + MONTHS[d.getMonth()] + " " + d.getDate());
  }

  function destroyCharts() {
    state.charts.forEach(function (c) { try { c.destroy(); } catch (e) {} });
    state.charts = [];
  }

  function setTab(name) {
    document.querySelectorAll(".tab").forEach(function (t) {
      t.classList.toggle("active", t.dataset.tab === name);
    });
  }

  /* ---------------- read streak (localStorage) ---------------- */

  function readSet() {
    try { return JSON.parse(localStorage.getItem("ga-read") || "{}"); }
    catch (e) { return {}; }
  }

  function markRead(date) {
    var r = readSet();
    if (!r[date]) {
      r[date] = 1;
      try { localStorage.setItem("ga-read", JSON.stringify(r)); } catch (e) {}
    }
  }

  function streakCount() {
    var r = readSet();
    var n = 0;
    for (var i = state.dates.length - 1; i >= 0; i--) {
      if (r[state.dates[i]]) n++;
      else break;
    }
    return n;
  }

  /* ---------------- day view ---------------- */

  function card(kicker, emoji, bodyHTML) {
    return '<article class="card"><h3 class="kicker"><span class="emoji">' + emoji +
      "</span>" + kicker + "</h3>" + bodyHTML + "</article>";
  }

  function renderDay(date) {
    setTab("today");
    state.current = date;
    flapDate(date);
    $dayNav.hidden = false;
    var i = state.dates.indexOf(date);
    $prevBtn.disabled = i <= 0;
    $nextBtn.disabled = i >= state.dates.length - 1;

    $view.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>';

    getReport(date).then(function (rep) {
      var s = rep.sections || {};
      var html = "";

      // read streak
      markRead(date);
      var streak = streakCount();
      if (streak >= 2) {
        html += '<div class="streak"><span class="streak-chip">🔥 ' + streak + "-day reading streak</span></div>";
      }

      if (s.stl_sports && s.stl_sports.teams && s.stl_sports.teams.length) {
        var lines = s.stl_sports.teams.map(function (t) {
          var bits = "";
          if (t.yesterday) {
            var y = t.yesterday;
            var res = y.draw ? "D" : (y.won ? "W" : "L");
            bits += "<div><span class='badge " + res + "'>" + res + "</span>" +
              esc(y.team_score) + "–" + esc(y.opp_score) + " " +
              (y.is_home ? "vs. " : "@ ") + esc(y.opponent) + "</div>";
          }
          if (t.next) {
            bits += "<div class='next-label'>next: <b>" + esc(t.next.label) + "</b> " +
              (t.next.is_home ? "vs. " : "@ ") + esc(t.next.opponent) + "</div>";
          }
          return "<div class='gameline'><span class='team-emoji'>" + t.emoji +
            "</span><span class='team-name'>" + esc(t.team) +
            "</span><div class='game-bits'>" + bits + "</div></div>";
        }).join("");
        html += '<article class="card board-card"><h3 class="kicker"><span class="emoji">🦁</span>St. Louis Sports</h3>' + lines + "</article>";
      }

      if (s.word) {
        html += card("Word of the Day", "📖",
          '<div class="word-head"><span class="word-word">' + esc(s.word.word) + "</span>" +
          (s.word.part_of_speech ? '<span class="word-pos">' + esc(s.word.part_of_speech) + "</span>" : "") +
          "</div><p class='word-def'>" + esc(s.word.definition) + "</p>" +
          (s.word.url ? '<p class="src-note"><a href="' + esc(s.word.url) + '" target="_blank" rel="noopener">Merriam-Webster ↗</a></p>' : ""));
      }

      if (s.sports_fact) {
        html += card("Sports Fact of the Day", "🏆",
          "<p class='body-text'>" + esc(s.sports_fact.text) + "</p>" +
          "<p class='src-note'>" + esc(s.sports_fact.sport) + "</p>");
      }

      if (s.market) {
        html += card("What's Moving the Market", "📰",
          "<p class='lead' style='font-size:18px'>" + esc(s.market.headline) + "</p>" +
          (s.market.summary ? "<p class='body-text' style='margin-top:6px'>" + esc(s.market.summary) + "</p>" : "") +
          "<p class='src-note'>" + esc(s.market.source) + "</p>");
      }

      if (s.quote) {
        html += card("Quote of the Day", "💬",
          "<p class='quote-text'>" + esc(s.quote.text) + "</p>" +
          (s.quote.author ? "<p class='quote-author'>" + esc(s.quote.author) + "</p>" : ""));
      }

      if (s.history) {
        html += card("This Day in History", "📜",
          "<p class='body-text'><strong>" + esc(s.history.year) + ".</strong> " + esc(s.history.text) + "</p>");
      }

      if (s.spotlight || s.song) {
        var chips = "";
        if (s.spotlight) {
          chips += '<div class="roster-chip"><div class="what">' +
            (s.spotlight.is_new ? "New spotlight this week" : "Spotlight this week") +
            '</div><div class="who">⭐ ' + esc(s.spotlight.persona) + "</div></div>";
        }
        if (s.song) {
          chips += '<div class="roster-chip"><div class="what">Picks today’s song</div>' +
            '<div class="who">🎵 ' + esc(s.song.persona) + "</div></div>";
        }
        html += card("The Roster", "🖐", '<div class="roster-row">' + chips + "</div>");
      }

      $view.innerHTML = html || '<p class="empty-note">No report for this day.</p>';
    }).catch(function () {
      $view.innerHTML = '<p class="empty-note">Couldn’t load this day’s report.</p>';
    });
  }

  function shiftDay(delta) {
    var i = state.dates.indexOf(state.current);
    var j = i + delta;
    if (j >= 0 && j < state.dates.length) {
      location.hash = "#/day/" + state.dates[j];
    }
  }

  $prevBtn.addEventListener("click", function () { shiftDay(-1); });
  $nextBtn.addEventListener("click", function () { shiftDay(1); });

  document.addEventListener("keydown", function (e) {
    if (!state.current || $dayNav.hidden) return;
    if (e.key === "ArrowLeft") shiftDay(-1);
    if (e.key === "ArrowRight") shiftDay(1);
  });

  // swipe between days
  var touchX = null, touchY = null;
  $view.addEventListener("touchstart", function (e) {
    if (e.touches.length === 1) {
      touchX = e.touches[0].clientX;
      touchY = e.touches[0].clientY;
    }
  }, { passive: true });
  $view.addEventListener("touchend", function (e) {
    if (touchX == null || $dayNav.hidden) return;
    var dx = e.changedTouches[0].clientX - touchX;
    var dy = e.changedTouches[0].clientY - touchY;
    if (Math.abs(dx) > 64 && Math.abs(dx) > Math.abs(dy) * 1.6) {
      shiftDay(dx < 0 ? 1 : -1); // swipe left -> next (newer)
    }
    touchX = touchY = null;
  }, { passive: true });

  /* ---------------- archive view ---------------- */

  var calCursor = null; // {y, m}

  function renderArchive() {
    setTab("archive");
    $dayNav.hidden = true;
    window.flapSet($flap, "ARCHIVE");
    destroyCharts();

    var latest = parseDate(state.dates[state.dates.length - 1]);
    var earliest = parseDate(state.dates[0]);
    if (!calCursor) calCursor = { y: latest.getFullYear(), m: latest.getMonth() };

    var html =
      '<input type="search" class="search-box" id="search" placeholder="Search every report…" autocomplete="off">' +
      '<div id="search-results"></div>' +
      '<div id="cal-zone"></div>';
    $view.innerHTML = html;

    drawCalendar(earliest, latest);

    var $s = document.getElementById("search");
    var t = null;
    $s.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () { runSearch($s.value.trim()); }, 220);
    });
  }

  function drawCalendar(earliest, latest) {
    var zone = document.getElementById("cal-zone");
    if (!zone) return;
    var y = calCursor.y, m = calCursor.m;
    var monthName = ["January", "February", "March", "April", "May", "June", "July",
      "August", "September", "October", "November", "December"][m];

    var atMin = y === earliest.getFullYear() && m === earliest.getMonth();
    var atMax = y === latest.getFullYear() && m === latest.getMonth();

    var html = '<div class="cal-head"><span class="cal-title">' + monthName + " " + y + "</span>" +
      '<span class="cal-btns">' +
      '<button class="cal-btn" id="cal-prev"' + (atMin ? " disabled" : "") + ">‹</button>" +
      '<button class="cal-btn" id="cal-next"' + (atMax ? " disabled" : "") + ">›</button>" +
      "</span></div>";

    html += '<div class="cal-grid">';
    DOWS.forEach(function (d) { html += '<div class="cal-dow">' + d[0] + "</div>"; });

    var first = new Date(y, m, 1);
    for (var i = 0; i < first.getDay(); i++) html += "<div></div>";
    var daysInMonth = new Date(y, m + 1, 0).getDate();
    var todayStr = state.dates[state.dates.length - 1];

    for (var day = 1; day <= daysInMonth; day++) {
      var ds = y + "-" + String(m + 1).padStart(2, "0") + "-" + String(day).padStart(2, "0");
      var has = state.dates.indexOf(ds) >= 0;
      var badge = (state.index.badges || {})[ds];
      var dot = has || badge ? '<span class="cal-dot' + (badge ? " " + badge : "") + '"></span>' : "";
      if (has) {
        html += '<a class="cal-cell has-report' + (ds === todayStr ? " today-cell" : "") +
          '" href="#/day/' + ds + '">' + day + dot + "</a>";
      } else {
        html += '<div class="cal-cell">' + day + dot + "</div>";
      }
    }
    html += "</div>";
    html += '<div class="cal-legend">' +
      '<span><span class="cal-dot W"></span>Cards win</span>' +
      '<span><span class="cal-dot L"></span>Cards loss</span>' +
      '<span><span class="cal-dot"></span>report</span></div>';

    zone.innerHTML = html;
    var prev = document.getElementById("cal-prev");
    var next = document.getElementById("cal-next");
    if (prev) prev.onclick = function () {
      calCursor.m--; if (calCursor.m < 0) { calCursor.m = 11; calCursor.y--; }
      drawCalendar(earliest, latest);
    };
    if (next) next.onclick = function () {
      calCursor.m++; if (calCursor.m > 11) { calCursor.m = 0; calCursor.y++; }
      drawCalendar(earliest, latest);
    };
  }

  function reportText(rep) {
    var s = rep.sections || {};
    var parts = [];
    if (s.word) parts.push(s.word.word + " " + s.word.definition);
    if (s.sports_fact) parts.push(s.sports_fact.text + " " + s.sports_fact.sport);
    if (s.market) parts.push(s.market.headline + " " + (s.market.summary || ""));
    if (s.quote) parts.push(s.quote.text + " " + (s.quote.author || ""));
    if (s.history) parts.push(s.history.year + " " + s.history.text);
    if (s.spotlight) parts.push("spotlight " + s.spotlight.persona);
    if (s.song) parts.push("song " + s.song.persona);
    if (s.stl_sports) (s.stl_sports.teams || []).forEach(function (t) {
      parts.push(t.team);
      if (t.yesterday) parts.push(t.yesterday.opponent);
      if (t.next) parts.push(t.next.opponent);
    });
    return parts.join(" • ");
  }

  function runSearch(q) {
    var box = document.getElementById("search-results");
    var zone = document.getElementById("cal-zone");
    if (!box) return;
    if (!q || q.length < 2) {
      box.innerHTML = "";
      if (zone) zone.style.display = "";
      return;
    }
    box.innerHTML = '<div class="skeleton" style="height:48px"></div>';
    getAllReports().then(function (reports) {
      var needle = q.toLowerCase();
      var hits = [];
      reports.forEach(function (rep) {
        var text = reportText(rep);
        var at = text.toLowerCase().indexOf(needle);
        if (at >= 0) {
          var start = Math.max(0, at - 46);
          hits.push({
            date: rep.date,
            display: rep.display_date,
            snip: (start > 0 ? "…" : "") +
              esc(text.slice(start, at)) +
              "<mark>" + esc(text.substr(at, q.length)) + "</mark>" +
              esc(text.slice(at + q.length, at + q.length + 90)),
          });
        }
      });
      hits.sort(function (a, b) { return a.date < b.date ? 1 : -1; });
      if (zone) zone.style.display = hits.length ? "none" : "";
      box.innerHTML = hits.length
        ? hits.map(function (h) {
            return '<a class="result-item" href="#/day/' + h.date + '">' +
              '<div class="result-date">' + esc(h.display) + "</div>" +
              '<div class="result-snip">' + h.snip + "…</div></a>";
          }).join("")
        : '<p class="empty-note">No matches in ' + state.dates.length + " reports.</p>";
    });
  }

  /* ---------------- stats view ---------------- */

  function loadChartJs() {
    if (state.chartsReady) return Promise.resolve();
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = "vendor/chart.umd.min.js";
      s.onload = function () { state.chartsReady = true; resolve(); };
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  var PALETTE = ["#c8102e", "#ffb81c", "#11294e", "#1f7a4d", "#7a4df0", "#e8743b"];

  function renderStats() {
    setTab("stats");
    $dayNav.hidden = true;
    window.flapSet($flap, "THE NUMBERS");
    destroyCharts();
    $view.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';

    Promise.all([getAllReports(), loadChartJs()]).then(function (res) {
      var reports = res[0];
      var s = computeStats(reports);
      var html = "";

      html += card("Cardinals Results", "⚾",
        s.strip.length
          ? '<div class="resultstrip">' + s.strip.map(function (r) {
              return '<span class="chip ' + r.badge + '" title="' + esc(r.date) + '">' + r.badge + "</span>";
            }).join("") + "</div><p class='stat-note'>" + s.record + " over the last " + s.strip.length + " games</p>"
          : "<p class='stat-note'>No games yet.</p>");

      html += card("Song Picker Tally", "🎵",
        '<div class="chart-wrap"><canvas id="ch-song" height="190"></canvas></div>' +
        "<p class='stat-note'>fair share ≈ " + s.songFair + " picks each</p>");

      html += card("Spotlight Rotation", "⭐",
        '<div class="chart-wrap"><canvas id="ch-spot" height="200"></canvas></div>' +
        "<p class='stat-note'>" + s.spotWeeks + " weeks so far</p>");

      html += card("Words Collected", "📖",
        '<div class="word-wall">' + s.words.map(function (w) {
          return '<a href="' + esc(w.url) + '" target="_blank" rel="noopener">' + esc(w.word.toLowerCase()) + "</a>";
        }).join("") + "</div>");

      html += card("Time Machine", "📜",
        '<div class="chart-wrap"><canvas id="ch-years" height="190"></canvas></div>' +
        "<p class='stat-note'>which centuries our history entries visit</p>");

      html += card("Fact Sport Mix", "🏆",
        '<div class="chart-wrap"><canvas id="ch-sports" height="' + (24 * s.sportMix.labels.length + 40) + '"></canvas></div>');

      html += card("Quote Roster", "💬",
        '<ul class="author-list">' + s.authors.map(function (a) {
          return "<li><span>" + esc(a[0]) + '</span><span class="n">×' + a[1] + "</span></li>";
        }).join("") + "</ul>");

      $view.innerHTML = html;

      var mono = { family: "'JetBrains Mono', monospace", size: 10 };

      state.charts.push(new Chart(document.getElementById("ch-song"), {
        type: "bar",
        data: {
          labels: s.song.labels,
          datasets: [{ data: s.song.values, backgroundColor: PALETTE, borderRadius: 6 }],
        },
        options: {
          plugins: { legend: { display: false } },
          scales: {
            y: { ticks: { stepSize: 1, font: mono }, grid: { color: "#e7decb" } },
            x: { ticks: { font: mono }, grid: { display: false } },
          },
        },
      }));

      state.charts.push(new Chart(document.getElementById("ch-spot"), {
        type: "doughnut",
        data: {
          labels: s.spot.labels,
          datasets: [{ data: s.spot.values, backgroundColor: PALETTE, borderWidth: 2, borderColor: "#fffdf7" }],
        },
        options: {
          cutout: "62%",
          plugins: { legend: { position: "right", labels: { font: mono, boxWidth: 12 } } },
        },
      }));

      state.charts.push(new Chart(document.getElementById("ch-years"), {
        type: "bar",
        data: {
          labels: s.eras.labels,
          datasets: [{ data: s.eras.values, backgroundColor: "#11294e", borderRadius: 6 }],
        },
        options: {
          plugins: { legend: { display: false } },
          scales: {
            y: { ticks: { stepSize: 1, font: mono }, grid: { color: "#e7decb" } },
            x: { ticks: { font: mono }, grid: { display: false } },
          },
        },
      }));

      state.charts.push(new Chart(document.getElementById("ch-sports"), {
        type: "bar",
        data: {
          labels: s.sportMix.labels,
          datasets: [{ data: s.sportMix.values, backgroundColor: "#c8102e", borderRadius: 6 }],
        },
        options: {
          indexAxis: "y",
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { stepSize: 1, font: mono }, grid: { color: "#e7decb" } },
            y: { ticks: { font: mono }, grid: { display: false } },
          },
        },
      }));
    }).catch(function (e) {
      $view.innerHTML = '<p class="empty-note">Stats unavailable: ' + esc(e.message) + "</p>";
    });
  }

  function computeStats(reports) {
    var songCounts = {}, spotByWeek = {}, words = [], eras = {}, authors = {}, sports = {};
    var strip = [];

    reports.forEach(function (rep) {
      var s = rep.sections || {};
      if (s.song) songCounts[s.song.persona] = (songCounts[s.song.persona] || 0) + 1;
      if (s.spotlight) {
        // one count per distinct week — key by the persona+week boundary via date math
        var d = parseDate(rep.date);
        var monday = new Date(d); monday.setDate(d.getDate() - ((d.getDay() + 6) % 7));
        spotByWeek[monday.toISOString().slice(0, 10)] = s.spotlight.persona;
      }
      if (s.word) words.push({ word: s.word.word, url: s.word.url || "#" });
      if (s.history && s.history.year != null) {
        var y = +s.history.year;
        var label = y < 1500 ? "pre-1500" : (Math.floor(y / 100) * 100) + "s";
        eras[label] = (eras[label] || 0) + 1;
      }
      if (s.quote && s.quote.author) authors[s.quote.author] = (authors[s.quote.author] || 0) + 1;
      if (s.sports_fact) sports[s.sports_fact.sport] = (sports[s.sports_fact.sport] || 0) + 1;
    });

    var badges = state.index.badges || {};
    Object.keys(badges).sort().forEach(function (d) {
      strip.push({ date: d, badge: badges[d] });
    });
    var w = strip.filter(function (r) { return r.badge === "W"; }).length;
    var l = strip.filter(function (r) { return r.badge === "L"; }).length;

    var spotCounts = {};
    Object.keys(spotByWeek).forEach(function (wk) {
      spotCounts[spotByWeek[wk]] = (spotCounts[spotByWeek[wk]] || 0) + 1;
    });

    function toSorted(obj) {
      var keys = Object.keys(obj).sort(function (a, b) { return obj[b] - obj[a]; });
      return { labels: keys, values: keys.map(function (k) { return obj[k]; }) };
    }

    var eraKeys = Object.keys(eras).sort(function (a, b) {
      var na = a === "pre-1500" ? 0 : parseInt(a, 10);
      var nb = b === "pre-1500" ? 0 : parseInt(b, 10);
      return na - nb;
    });

    return {
      song: toSorted(songCounts),
      songFair: Math.round(reports.length / 6 * 10) / 10,
      spot: toSorted(spotCounts),
      spotWeeks: Object.keys(spotByWeek).length,
      words: words.reverse(),
      eras: { labels: eraKeys, values: eraKeys.map(function (k) { return eras[k]; }) },
      authors: Object.keys(authors).sort(function (a, b) { return authors[b] - authors[a]; })
        .slice(0, 10).map(function (k) { return [k, authors[k]]; }),
      sportMix: toSorted(sports),
      strip: strip,
      record: w + "-" + l + (strip.length - w - l > 0 ? "-" + (strip.length - w - l) : ""),
    };
  }

  /* ---------------- router ---------------- */

  function route() {
    var h = location.hash || "#/today";
    destroyCharts();
    if (h.indexOf("#/day/") === 0) {
      var d = h.slice(6);
      if (state.dates.indexOf(d) >= 0) return renderDay(d);
      return renderDay(state.index.latest);
    }
    if (h === "#/archive") return renderArchive();
    if (h === "#/stats") return renderStats();
    return renderDay(state.index.latest);
  }

  window.addEventListener("hashchange", route);

  /* ---------------- boot ---------------- */

  // legacy ?date= permalinks -> hash
  var qd = new URLSearchParams(location.search).get("date");
  if (qd) {
    history.replaceState(null, "", location.pathname + "#/day/" + qd);
  }

  window.flapSet($flap, "LOADING");

  fetchJSON("data/index.json").then(function (index) {
    state.index = index;
    state.dates = index.dates.slice().sort();
    route();
  }).catch(function () {
    $view.innerHTML = '<p class="empty-note">No data yet. Run the daily report once.</p>';
    window.flapSet($flap, "NO DATA");
  });

  if ("serviceWorker" in navigator && location.protocol === "https:") {
    navigator.serviceWorker.register("sw.js").catch(function () {});
  }
})();
