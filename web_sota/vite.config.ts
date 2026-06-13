import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ['goliath'],
    port: 10860,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api/logs": {
        target: "http://127.0.0.1:11066",
        changeOrigin: true,
      },
      "/api": {
        target: "http://127.0.0.1:10861",
        changeOrigin: true,
      },
    },
  },
});
