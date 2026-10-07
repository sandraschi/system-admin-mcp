/**
 * Backend base URL, fleet standard (1F + Tauri §B):
 * same-origin ("") in a browser tab so calls ride the Vite /api proxy,
 * absolute operator loopback in the Tauri WebView (no proxy there).
 * The operator port (11240, system-admin-mcp-native) is baked at build;
 * it is deliberately NOT the dev backend port (10861, side-by-side rule).
 * A hardcoded absolute URL breaks every non-localhost tab (LAN name,
 * Tailscale MagicDNS, `goliath`) on CORS while curl "proves" health.
 */
function isTauri(): boolean {
  if (typeof window === "undefined") return false;
  const w = window as unknown as Record<string, unknown>;
  return "__TAURI__" in w || "__TAURI_INTERNALS__" in w;
}

const API_BASE = isTauri() ? "http://127.0.0.1:11240" : "";
export default API_BASE;
