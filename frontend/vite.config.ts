import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// API base can be overridden at build time: VITE_API_BASE=https://api.example.com
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "robots.txt"],
      manifest: {
        name: "Salama — Community Safety",
        short_name: "Salama",
        description: "Offline-first community emergency alerts, hazard map, and neighbor check-ins.",
        theme_color: "#0f766e",
        background_color: "#0b1120",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" }
        ]
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/api/"),
            handler: "NetworkFirst",
            options: { cacheName: "salama-api", networkTimeoutSeconds: 5 }
          }
        ]
      }
    })
  ],
  server: { host: true, port: 5173 },
  preview: { host: true, port: 4173 }
});
