import { defineConfig } from "vitepress";

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Graphite Theme",
  titleTemplate: ":title",
  description: "Calm and clean theme for Home Assistant.",
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
