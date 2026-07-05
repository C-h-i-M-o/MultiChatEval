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
          if (id.includes("/antd/es/table/") || id.includes("/antd/es/table")) {
            return "antd-table";
          }
          if (
            id.includes("/antd/es/form/") ||
            id.includes("/antd/es/modal/") ||
            id.includes("/antd/es/drawer/") ||
            id.includes("/antd/es/popconfirm/") ||
            id.includes("/antd/es/message/")
          ) {
            return "antd-feedback";
          }
          if (id.includes("/antd/es/select/") || id.includes("/antd/es/select")) {
            return "antd-select";
          }
          if (
            id.includes("/antd/es/input/") ||
            id.includes("/antd/es/input") ||
            id.includes("/antd/es/input-number/") ||
            id.includes("/antd/es/input-number")
          ) {
            return "antd-input";
          }
          if (id.includes("/antd/es/button/") || id.includes("/antd/es/button")) {
            return "antd-button";
          }
          if (
            id.includes("/antd/es/switch/") ||
            id.includes("/antd/es/switch") ||
            id.includes("/antd/es/segmented/") ||
            id.includes("/antd/es/segmented")
          ) {
            return "antd-controls";
          }
          if (
            id.includes("/antd/es/card/") ||
            id.includes("/antd/es/statistic/") ||
            id.includes("/antd/es/pagination/") ||
            id.includes("/antd/es/tag/") ||
            id.includes("/antd/es/tabs/") ||
            id.includes("/antd/es/space/") ||
            id.includes("/antd/es/row/") ||
            id.includes("/antd/es/col/") ||
            id.includes("/antd/es/config-provider/") ||
            id.includes("/antd/es/locale/")
          ) {
            return "antd-display";
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
