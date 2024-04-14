import { resolve } from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import * as packageJson from "./package.json";
// https://vitejs.dev/config/
export default defineConfig((configEnv) => ({
  plugins: [react()],
  build: {
    lib: {
      entry: resolve("src", "Root.jsx"),
      name: "Library",
      formats: ["es", "umd"],
      fileName: (format) => `library.${format}.js`,
    },
    rollupOptions: {
      external: [...Object.keys(packageJson.peerDependencies)],
    },
  },
}));
