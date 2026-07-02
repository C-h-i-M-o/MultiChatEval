import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const devServerPort = Number(process.env.VITE_DEV_PORT || 5173);
const backendTarget = process.env.VITE_BACKEND_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [vue()],
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
