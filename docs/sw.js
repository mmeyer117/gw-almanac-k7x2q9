/* Minimal service worker: cache-first shell, network-first data. */
var VERSION = "ga-v2";
var SHELL = [
  "./",
  "index.html",
  "css/style.css",
  "js/app.js",
  "js/flap.js",
  "js/share.js",
  "vendor/chart.umd.min.js",
  "manifest.webmanifest",
  "icons/icon.svg",
];

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(VERSION).then(function (c) { return c.addAll(SHELL); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== VERSION; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;

  if (url.pathname.indexOf("/data/") >= 0) {
    // data: network first, fall back to cache (offline reads yesterday's copy)
    e.respondWith(
      fetch(e.request).then(function (resp) {
        var copy = resp.clone();
        caches.open(VERSION).then(function (c) { c.put(e.request, copy); });
        return resp;
      }).catch(function () { return caches.match(e.request); })
    );
  } else {
    // shell: cache first
    e.respondWith(
      caches.match(e.request).then(function (hit) {
        return hit || fetch(e.request).then(function (resp) {
          var copy = resp.clone();
          caches.open(VERSION).then(function (c) { c.put(e.request, copy); });
          return resp;
        });
      })
    );
  }
});
