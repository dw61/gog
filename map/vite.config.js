import { defineConfig } from 'vite'
import { fileURLToPath } from 'node:url'
import tailwindcss from '@tailwindcss/vite'

const projectRoot = fileURLToPath(new URL('../', import.meta.url))

export default defineConfig({
  root: projectRoot,
  publicDir: false,
  plugins: [tailwindcss()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        map: `${projectRoot}index.html`,
        about: `${projectRoot}about/index.html`,
        review: `${projectRoot}review/index.html`,
      },
    },
  },
})
