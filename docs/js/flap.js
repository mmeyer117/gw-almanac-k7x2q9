/* Split-flap display: renders a string as flip tiles in a container.
   Characters animate per-cell with a stagger, like an airport board. */
(function () {
  "use strict";

  var FLAP_CHARS = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,.";
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function makeCell(ch) {
    var cell = document.createElement("div");
    cell.className = "flap-cell" + (ch === " " ? " space" : "");
    cell.dataset.ch = ch;
    if (ch !== " ") {
      cell.innerHTML =
        '<div class="flap-half flap-top"><span>' + ch + "</span></div>" +
        '<div class="flap-half flap-bottom"><span>' + ch + "</span></div>";
    }
    return cell;
  }

  function flipCell(cell, toCh, delay) {
    var fromCh = cell.dataset.ch || " ";
    if (fromCh === toCh) return;
    cell.dataset.ch = toCh;

    if (toCh === " " || fromCh === " " || reducedMotion) {
      // structural change or reduced motion: swap instantly
      var fresh = makeCell(toCh);
      cell.className = fresh.className;
      cell.innerHTML = fresh.innerHTML;
      cell.dataset.ch = toCh;
      return;
    }

    setTimeout(function () {
      // Bottom shows OLD char until new bottom flips down over it
      cell.innerHTML =
        '<div class="flap-half flap-top"><span>' + toCh + "</span></div>" +
        '<div class="flap-half flap-bottom"><span>' + fromCh + "</span></div>" +
        '<div class="flap-half flap-top flap-flip-top"><span>' + fromCh + "</span></div>" +
        '<div class="flap-half flap-bottom flap-flip-bottom"><span>' + toCh + "</span></div>";
      setTimeout(function () {
        cell.innerHTML =
          '<div class="flap-half flap-top"><span>' + toCh + "</span></div>" +
          '<div class="flap-half flap-bottom"><span>' + toCh + "</span></div>";
      }, 420);
    }, delay);
  }

  /** Set the board's text. Container keeps cell count of the longest string shown. */
  window.flapSet = function (container, text) {
    text = text.toUpperCase();
    var cells = container.children;

    // grow/shrink cell count to match
    while (cells.length < text.length) {
      container.appendChild(makeCell(" "));
    }
    while (cells.length > text.length) {
      container.removeChild(container.lastChild);
    }
    for (var i = 0; i < text.length; i++) {
      var ch = FLAP_CHARS.indexOf(text[i]) >= 0 ? text[i] : " ";
      flipCell(cells[i], ch, i * 36);
    }
  };
})();
