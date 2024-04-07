import { defineConfig } from 'vite'

export default defineConfig({
  mode: "development",
  build: {
    outDir: "../static",
    minify: false,
    rollupOptions: {
      input: "map.jsx",
      output: {
        entryFileNames: '[name].js',
      },
    },
  },
})
