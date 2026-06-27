const CACHE_NAME = "fitfresh-v1"; // Defines the current cache version identifier to manage asset storage updates
const ASSETS_TO_CACHE = ["/", "/offline", "/manifest.json", "/static/style.css", "/static/images/icon-192.png", "/static/images/icon-512.png"]; // Lists all essential file paths and landing endpoints that must be available for offline operation

// Fires when the service worker finishes setup, pre-loading all core assets into temporary browser memory
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
  self.skipWaiting(); // Forces the newly updated service worker to take control of the browser tab immediately
});

// Cleans out outdated cache storage containers from previous website versions when a new worker becomes active
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : null)))
    )
  );
  self.clients.claim(); // Takes absolute control of all open browser windows immediately without waiting for a manual refresh
});

// Intercepts every outgoing browser network connection to handle offline resource loading smoothly
self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return; // Bypasses resource intercept tracking completely for state-changing network submissions like database updates
  if (!request.url.startsWith(self.location.origin)) return; // Restricts local background caching mechanics to files hosted exclusively on this website's server
  event.respondWith(
    fetch(request) // Attempts to fetch the absolute latest copy of the requested asset live from the network
      .then((networkResponse) => {
        const copy = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)); // Saves a fresh copy of the successfully fetched network asset into local memory for next time
        return networkResponse;
      })

      // Triggers fallback recovery protocols automatically if a live network connection cannot be reached
      .catch(() => {
        return caches.match(request).then((cached) => {
          if (cached) return cached; // Serves the saved asset instantly from storage memory if a matching copy was recorded previously
          
          // Directs the browser window to load the customized standby page if a page transition breaks offline
          if (request.mode === "navigate") {
            return caches.match("/offline");
          }
          return new Response("Offline", { status: 503, statusText: "Offline" }); // Issues a standard browser failure packet block if background image or script resources fail to load offline
        });
      })
  );
});