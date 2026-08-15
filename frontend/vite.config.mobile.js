import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  base: './',
  server: {
    port: 5174,
    strictPort: true
  },
  build: {
    outDir: 'dist-mobile',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      input: 'index.mobile.html'
    }
  },
  plugins: [
    vue(),
    AutoImport({
      resolvers: [AntDesignVueResolver()],
    }),
    Components({
      resolvers: [AntDesignVueResolver({ importStyle: false })],
    }),
    {
      name: 'shared-to-mobile',
      enforce: 'pre',
      resolveId(id, importer) {
        const mobileRoot = fileURLToPath(new URL('./src-mobile', import.meta.url))
        const sharedRoot = fileURLToPath(new URL('./src', import.meta.url))
        const redirectMap = {
          'utils/request': 'utils/request.js',
          'utils/request.js': 'utils/request.js',
          'utils/tts': 'utils/tts.js',
          'utils/tts.js': 'utils/tts.js',
          'utils/healthTrendFormat.mjs': 'utils/healthTrendFormat.mjs',
          'utils/healthTestFlow.mjs': 'utils/healthTestFlow.mjs'
        }
        if (id && id.startsWith(sharedRoot)) {
          const relative = id.slice(sharedRoot.length + 1)
          const mobileFile = redirectMap[relative]
          if (mobileFile) {
            return `${mobileRoot}/${mobileFile}`
          }
        }
      }
    }
  ],
  resolve: {
    alias: [
      { find: '@', replacement: fileURLToPath(new URL('./src-mobile', import.meta.url)) },
      { find: '@shared', replacement: fileURLToPath(new URL('./src', import.meta.url)) }
    ]
  }
})
