import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Graphite Theme",
  titleTemplate: ":title",
  description: "Calm and clean theme for Home Assistant.",
  head: [
    ['link', { rel: 'icon', href: '/assets/favicon/favicon.ico' }],
    ['link', { rel: "shortcut icon", href: "/assets/favicons/favicon.ico"}],
    ['link', { rel: "apple-touch-icon", sizes: "180x180", href: "/assets/favicons/apple-touch-icon.png"}],
    ['link', { rel: "icon", type: "image/png", sizes: "96x96", href: "/assets/favicons/favicon-96x96.png"}],
    ['link', { rel: "icon", type: "image/png", sizes: "192x192", href: "/assets/favicons/favicon-192x192.png"}],
    ['link', { rel: "icon", type: "image/png", sizes: "512x512", href: "/assets/favicons/favicon-512x512.png"}],
    ['link', { rel: "manifest", href: "/assets/favicons/site.webmanifest"}],
    ['meta', { name: "google-site-verification", content: "xGadaEB3oxAJxExOWGecimtRzY1i11cdAP4m8ulj-io"}],
  ],
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: "Home", link: "/" },
      { text: "Get Started", link: "/guides/getting-started" },
      { text: "Theme Patcher", link: "/features/graphite-theme-patcher" },
      { text: "Development Kit", link: "/features/graphite-theme-development-kit" },
      { text: "Card Examples", link: "/guides/card-examples" },
      { text: "About", link: "/about/graphite" },
    ],
    socialLinks: [
      { icon: "github", link: "https://github.com/TilmanGriesel/graphite" },
    ],
    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024 Tilman Griesel'
    }
  },
});
