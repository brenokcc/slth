import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          if (id.includes("node_modules")) return "react";
          if (id.includes("slth/src/reactjs/src/")) return "slth";
          if (id.includes("service-worker")) return "service-worker";
        },
        dir: "tmp",
        entryFileNames: `js/[name].min.js`,
        chunkFileNames: `js/[name].min.js`,
        assetFileNames: `js/[name].min.[ext]`,
      },
    },
  },
});
