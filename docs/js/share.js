/* Copy-for-chat: rebuilds the plain-text daily message from a day's JSON,
   exactly mirroring the Python text renderer (src/report.py).

   Privacy: personas can be remapped to real display names via a small
   settings panel stored ONLY in this browser's localStorage — nothing is
   ever sent anywhere or committed anywhere. Without saved names, the copied
   text uses personas. */
(function () {
  "use strict";

  var DEFAULT_HEADER = "🗞️ THE GATEWAY ALMANAC";

  function prefs() {
    try { return JSON.parse(localStorage.getItem("ga-chat-prefs") || "{}"); }
    catch (e) { return {}; }
  }

  function savePrefs(p) {
    try { localStorage.setItem("ga-chat-prefs", JSON.stringify(p)); } catch (e) {}
  }

  function mapName(persona) {
    var names = prefs().names || {};
    return names[persona] || persona;
  }

  function trimQuote(q) {
    if (q.length <= 250) return q;
    var first = q.split(/(?<=[.!?])\s+/)[0];
    if (first.length <= 250) return first;
    var cut = q.slice(0, 240);
    cut = cut.slice(0, cut.lastIndexOf(" "));
    return cut.replace(/[ ,;:]+$/, "") + "...";
  }

  window.buildChatText = function (rep) {
    var s = rep.sections || {};
    var blocks = [(prefs().header || DEFAULT_HEADER) + "\n" + rep.display_date];

    if (s.word) {
      var pos = s.word.part_of_speech ? " (" + s.word.part_of_speech + ")" : "";
      blocks.push("📖 WORD OF THE DAY\n" + s.word.word.toUpperCase() + pos + " — " + s.word.definition);
    }
    if (s.sports_fact) {
      blocks.push("🏆 SPORTS FACT OF THE DAY\n" + s.sports_fact.text);
    }
    if (s.stl_sports && s.stl_sports.teams && s.stl_sports.teams.length) {
      var lines = s.stl_sports.teams.map(function (t) {
        var parts = [];
        if (t.yesterday) {
          var y = t.yesterday;
          var res = y.draw ? "D" : (y.won ? "W" : "L");
          parts.push("Yesterday: " + res + " " + y.team_score + "-" + y.opp_score + " " +
            (y.is_home ? "vs. " : "@ ") + y.opponent);
        }
        if (t.next) {
          parts.push("Next: " + t.next.label + " " + (t.next.is_home ? "vs." : "@") + " " + t.next.opponent);
        }
        return t.emoji + " " + t.team + ": " + parts.join(" | ");
      });
      blocks.push("🦁 ST. LOUIS SPORTS\n" + lines.join("\n"));
    }
    if (s.market) {
      var head = s.market.headline.replace(/\.+$/, "");
      blocks.push("📰 WHAT'S MOVING THE MARKET\n" + head + "." +
        (s.market.summary ? " " + s.market.summary : ""));
    }
    if (s.quote) {
      blocks.push("💬 QUOTE OF THE DAY\n\"" + trimQuote(s.quote.text) + "\"" +
        (s.quote.author ? " — " + s.quote.author : ""));
    }
    if (s.history) {
      blocks.push("📜 THIS DAY IN HISTORY\nOn this day in " + s.history.year + ", " + s.history.text);
    }
    if (s.spotlight) {
      blocks.push("⭐ SPOTLIGHT\n" +
        (s.spotlight.is_new ? "This week's spotlight: " : "This week: ") +
        mapName(s.spotlight.persona));
    }
    if (s.song) {
      blocks.push("🎵 SONG OF THE DAY\n" + mapName(s.song.persona));
    }
    return blocks.join("\n\n");
  };

  window.copyChatText = function (rep, btn) {
    var text = window.buildChatText(rep);
    var done = function (ok) {
      var orig = btn.textContent;
      btn.textContent = ok ? "Copied ✓" : "Copy failed";
      btn.disabled = true;
      setTimeout(function () { btn.textContent = orig; btn.disabled = false; }, 1600);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { done(true); },
        function () { done(fallbackCopy(text)); });
    } else {
      done(fallbackCopy(text));
    }
  };

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
    return ok;
  }

  /* settings panel HTML for the day view */
  window.chatSettingsHTML = function (personas) {
    var p = prefs();
    var names = p.names || {};
    var rows = personas.map(function (per) {
      return '<label class="names-row"><span>' + per + ' →</span>' +
        '<input data-persona="' + per + '" value="' + (names[per] || "").replace(/"/g, "&quot;") +
        '" placeholder="' + per + '" autocomplete="off"></label>';
    }).join("");
    return '<details class="chat-setup"><summary>⚙ chat names (stored only on this device)</summary>' +
      '<div class="names-grid">' +
      '<label class="names-row"><span>header</span>' +
      '<input id="pref-header" value="' + (p.header || "").replace(/"/g, "&quot;") +
      '" placeholder="' + DEFAULT_HEADER + '" autocomplete="off"></label>' +
      rows +
      '<button class="save-names" id="save-names">Save</button>' +
      "</div></details>";
  };

  window.bindChatSettings = function (container) {
    var btn = container.querySelector("#save-names");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var names = {};
      container.querySelectorAll("input[data-persona]").forEach(function (inp) {
        if (inp.value.trim()) names[inp.dataset.persona] = inp.value.trim();
      });
      var header = container.querySelector("#pref-header").value.trim();
      savePrefs({ names: names, header: header || undefined });
      btn.textContent = "Saved ✓";
      setTimeout(function () { btn.textContent = "Save"; }, 1400);
    });
  };
})();
