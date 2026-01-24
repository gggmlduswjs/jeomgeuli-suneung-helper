// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'pwa-192x192.png', 'pwa-512x512.png'],
      manifest: {
        name: '점글이 - 시각장애인 정보접근 PWA',
        short_name: '점글이',
        description: '시각장애인을 위한 정보접근 및 점자학습 PWA',
        theme_color: '#ffffff',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ],
        categories: ['education', 'accessibility'],
        shortcuts: [
          {
            name: '정보 탐색',
            short_name: '탐색',
            description: '정보 탐색 페이지로 이동',
            url: '/explore',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          },
          {
            name: '점자 학습',
            short_name: '학습',
            description: '점자 학습 페이지로 이동',
            url: '/learn',
            icons: [{ src: 'pwa-192x192.png', sizes: '192x192' }]
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,ico,png,svg,woff2}'],
        globIgnores: ['**/index.html'],
        navigateFallback: '/index.html',
        navigateFallbackAllowlist: [/^\/$/, /^\/admin/, /^\/books/, /^\/summary/, /^\/main/, /^\/book/, /^\/lesson/, /^\/unit/, /^\/literature/, /^\/curriculum/],
        navigateFallbackDenylist: [/^\/api\/.*/, /^\/_\/.*/],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1년
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'gstatic-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1년
              }
            }
          },
          {
            urlPattern: /^http:\/\/localhost:8000\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              networkTimeoutSeconds: 10,
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      },
      devOptions: {
        enabled: true,
        type: 'module'
      }
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api/v1": {
        target: process.env.API_BASE_URL || "http://localhost:8000",
        changeOrigin: true,
        timeout: 300000, // 5분 타임아웃 (PDF 처리용)
        proxyTimeout: 300000,
      },
      // 레거시 Django API (점진적 전환)
      "/api": {
        target: process.env.API_BASE_URL || "http://localhost:8000",
        changeOrigin: true,
        timeout: 300000,
        proxyTimeout: 300000,
      },
    },
    hmr: { host: "localhost", protocol: "ws" }
  },
});
