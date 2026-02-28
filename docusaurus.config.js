// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const {themes} = require('prism-react-renderer');
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Knowledge Base',
  tagline: 'Curated technology knowledge for developers',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://your-username.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/knowledge-base/',

  // GitHub pages deployment config.
  organizationName: 'your-org', // Usually your GitHub org/user name.
  projectName: 'knowledge-base', // Usually your repo name.

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          path: 'content',
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/your-org/knowledge-base/edit/main/',
        },
        blog: false,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'Knowledge Base',
        logo: {
          alt: 'Knowledge Base Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'dropdown',
            label: 'AI',
            position: 'left',
            items: [
              {to: '/ai/beginner', label: 'Beginner'},
              {to: '/ai/intermediate', label: 'Intermediate'},
              {to: '/ai/master', label: 'Master'},
            ],
          },
          {
            type: 'dropdown',
            label: 'Blockchain',
            position: 'left',
            items: [
              {to: '/blockchain/beginner', label: 'Beginner'},
              {to: '/blockchain/intermediate', label: 'Intermediate'},
              {to: '/blockchain/master', label: 'Master'},
            ],
          },
          {
            type: 'dropdown',
            label: 'Protocol',
            position: 'left',
            items: [
              {to: '/protocol/beginner', label: 'Beginner'},
              {to: '/protocol/intermediate', label: 'Intermediate'},
              {to: '/protocol/master', label: 'Master'},
            ],
          },
          {
            href: 'https://github.com/your-org/knowledge-base',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Domains',
            items: [
              {label: 'AI', to: '/ai'},
              {label: 'Blockchain', to: '/blockchain'},
              {label: 'Protocol', to: '/protocol'},
            ],
          },
          {
            title: 'Learning Paths',
            items: [
              {label: 'Beginner', to: '/'},
              {label: 'Intermediate', to: '/'},
              {label: 'Master', to: '/'},
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/your-org/knowledge-base',
              },
              {
                label: 'Contribute',
                href: 'https://github.com/your-org/knowledge-base/issues',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Knowledge Base. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['python', 'bash', 'yaml', 'json'],
      },
      algolia: {
        // If you want to add Algolia search later
        // appId: 'YOUR_APP_ID',
        // apiKey: 'YOUR_SEARCH_API_KEY',
        // indexName: 'YOUR_INDEX_NAME',
      },
    }),
};

module.exports = config;
