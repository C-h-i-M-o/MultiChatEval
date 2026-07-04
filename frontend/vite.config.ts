import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const devServerPort = Number(process.env.VITE_DEV_PORT || "5174");
const backendTarget = process.env.VITE_BACKEND_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rolldownOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (id.includes("/react/") || id.includes("/react-dom/") || id.includes("/react-router-dom/")) {
            return "react-vendor";
          }
          if (id.includes("/@ant-design/icons/")) {
            return "antd-icons";
          }
          if (id.includes("/@ant-design/") || id.includes("/@ant-design-cssinjs/")) {
            return "antd-style";
          }
          if (id.includes("/rc-")) {
            return "rc-vendor";
          }
          if (id.includes("/antd/")) {
            return "antd-core";
          }
          if (id.includes("/recharts/") || id.includes("/d3-") || id.includes("/victory-vendor/")) {
            return "chart-vendor";
          }
          if (id.includes("/gsap/") || id.includes("/@gsap/")) {
            return "animation-vendor";
          }
          if (id.includes("/markdown-it/") || id.includes("/dompurify/")) {
            return "markdown-vendor";
          }
          return "vendor";
        }
      }
    }
  },
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
