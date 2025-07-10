# SiPeka Frontend

This is the frontend for **SiPeka**, a web application built with [Next.js](https://nextjs.org/). The project leverages modern web technologies and a modular structure to ensure scalability and maintainability.

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Available Scripts](#available-scripts)
- [Customization](#customization)
- [Learn More](#learn-more)
- [License](#license)

## Project Overview

**SiPeka** is a web application designed to provide a robust and user-friendly interface. The frontend is built using Next.js, offering server-side rendering, static site generation, and a seamless developer experience.

## Features

- ⚡ Fast and optimized with Next.js
- 🎨 Custom UI components (Button, Card, etc.)
- 🌐 Modern CSS with global styles
- 🗂️ Modular and scalable folder structure
- 🛠️ Easy to extend and maintain

## Project Structure

```
.
├── app/                # Next.js app directory (routing, pages, layouts)
│   ├── favicon.ico
│   ├── globals.css     # Global styles
│   ├── layout.tsx      # Root layout
│   └── page.tsx        # Main landing page
├── components/         # Reusable UI components
│   └── ui/
│       ├── button.tsx
│       └── card.tsx
├── lib/                # Utility functions and libraries
│   └── utils.ts
├── public/             # Static assets (SVGs, images)
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── package.json        # Project metadata and scripts
├── tsconfig.json       # TypeScript configuration
├── next.config.ts      # Next.js configuration
├── postcss.config.mjs  # PostCSS configuration
├── components.json     # Component registry (if used)
├── bun.lock            # Bun package manager lockfile
└── README.md           # Project documentation
```

## Getting Started

### Prerequisites

- Node.js, Bun, Yarn, or PNPM installed
- (Optional) Familiarity with TypeScript and React

### Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn
   # or
   pnpm install
   # or
   bun install
   ```

3. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   # or
   bun dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Available Scripts

- `dev` – Start the development server
- `build` – Build the application for production
- `start` – Start the production server
- `lint` – Run ESLint for code quality

## Customization

- **UI Components:** Add or modify components in `components/ui/`.
- **Global Styles:** Edit `app/globals.css` for global CSS.
- **Utilities:** Place shared functions in `lib/utils.ts`.
- **Static Assets:** Add images or SVGs to the `public/` directory.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## License

This project is licensed under the MIT License.
