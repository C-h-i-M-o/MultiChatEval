import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const devServerPort = Number(process.env.VITE_DEV_PORT || "5174");
const backendTarget = process.env.VITE_BACKEND_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: devServerPort,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
});
