/**
 * Backend base URL, fleet standard (1F):
 * same-origin ("") in a browser tab so calls ride the Vite /api proxy,
 * absolute loopback only inside the Tauri WebView (no proxy there).
 * A hardcoded absolute URL breaks every non-localhost tab (LAN name,
 * Tailscale MagicDNS, `goliath`) on CORS while curl "proves" health.
 */
function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as unknown as Record<string, unknown>;
  return "__TAURI__" in w || "__TAURI_INTERNALS__" in w;
}

const API_BASE = isTauri() ? "http://127.0.0.1:10861" : "";
export default API_BASE;
