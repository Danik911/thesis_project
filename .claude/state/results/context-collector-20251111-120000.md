# Context Collector Result - 20251111-120000

## Agent Configuration
- Agent: context-collector
- Task ID: 2.1
- Invoked: 2025-11-11T12:00:00Z
- Duration: 20 minutes
- Status: SUCCESS

## Task Understanding

Task 2.1 aims to initialize a Next.js 14 frontend project with TypeScript and Tailwind CSS under `main/frontend`, configured for static export (`output: 'export'`) to enable S3 static hosting deployment. The frontend will integrate with the existing FastAPI backend (Task 1.3) and use Clerk authentication (Task 1.4) for user management. The project requires compliance-focused branding suitable for pharmaceutical regulatory contexts, with environment variable handling for Clerk publishable key and API base URL.

**Critical Architecture Match:** The research reveals that static export + Clerk integration requires a **client-side authentication pattern** where the static Next.js app authenticates users in the browser and calls the authenticated FastAPI backend with JWT tokens. This architecture aligns perfectly with the existing Task 1.4 implementation (FastAPI backend with Clerk JWT verification).

## Research Findings

### Next.js 14 App Router + Static Export Patterns

**Latest Stable Version:** Next.js 14.2.33 (latest patch in 14.2.x series as of November 2025)

**Static Export Configuration:**
The modern approach uses `output: 'export'` in `next.config.mjs` (or `.ts`), replacing the deprecated `next export` command. This setting instructs Next.js to generate static HTML files during `next build`, creating an `out/` directory suitable for deployment to any static host (S3, nginx, GitHub Pages).

**Required next.config.mjs Configuration:**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',              // Enable static export
  trailingSlash: true,           // S3-compatible URLs (/blog/ vs /blog)
  images: {
    unoptimized: true,           // Required: no runtime image optimization
  },
  // Optional but recommended:
  // distDir: 'out',             // Output directory (default)
};

module.exports = nextConfig;
```

**TypeScript Configuration Alternative:**
```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig
```

**Static Export Limitations (CRITICAL):**
- NO server-side features: `getServerSideProps`, middleware, API routes (Route Handlers), Server Actions
- NO runtime image optimization (must use `images: { unoptimized: true }` or custom loaders)
- NO dynamic routes without `generateStaticParams` function
- NO cookies, rewrites, redirects, headers (runtime server operations)
- NO Incremental Static Regeneration (ISR)
- NO Draft Mode, Intercepting Routes

**What DOES Work with Static Export:**
- Server Components (execute at build time, not runtime)
- Client Components (marked with 'use client')
- Static generation of dynamic routes via `generateStaticParams`
- Client-side data fetching (SWR, React Query)
- Static Route Handlers (with `export const dynamic = 'force-static'`)

**trailingSlash Importance for S3:**
Setting `trailingSlash: true` ensures routes generate as `index.html` files within folders (e.g., `/blog/post-1/index.html` rather than `/blog/post-1.html`). This aligns with S3 static website hosting URL resolution, where `/blog/post-1/` automatically resolves to `/blog/post-1/index.html`.

**Sources:**
- https://nextjs.org/docs/app/guides/static-exports
- https://github.com/vercel/next.js/blob/canary/docs/01-app/02-guides/static-exports.mdx
- https://nextjs.org/blog/next-14-2

---

### Clerk React SDK Integration with Static Export

**CRITICAL FINDING: Fundamental Incompatibility**

Clerk authentication and Next.js static export are **fundamentally incompatible** in their default configurations. Static export generates HTML at build time, while Clerk's authentication architecture requires:
- Runtime server middleware (`clerkMiddleware()`)
- Request-time cookie management
- Dynamic route protection
- Server-side JWT verification

**None of these features are available in static export deployments** because static HTML is served from commodity web servers (nginx, S3) without a Node.js runtime.

**Solution: Client-Side Authentication Pattern**

The viable approach for static exports is implementing authentication **entirely on the client side** using:
- `<ClerkProvider>` wrapper in root layout
- Client-side components: `<SignIn />`, `<SignUp />`, `<UserButton />`
- Client-side hooks: `useAuth()`, `useUser()`
- JWT token retrieval via `getToken()` for API calls

**This pattern works perfectly with the existing architecture:**
1. Static Next.js frontend authenticates users in browser
2. User obtains JWT token via `getToken()`
3. Frontend calls FastAPI backend with `Authorization: Bearer {token}` header
4. Backend validates JWT using Clerk's public keys (already implemented in Task 1.4)

**Package Version:** `@clerk/nextjs@^5.0.0`
- Version 5.x (Core 2) is the latest stable as of November 2025
- Version 6.x exists but introduces breaking changes (async `auth()`, async `clerkClient()`)
- Recommendation: Use v5.x for stability

**Environment Variables Required:**
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
```
- Must use `NEXT_PUBLIC_` prefix for client-side access
- Value is embedded in static bundle at build time
- Already configured in `.env.local` from Task 1.4

**ClerkProvider Setup (app/layout.tsx):**
```typescript
import { ClerkProvider } from '@clerk/nextjs';
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Pharmaceutical Test Generation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

**Client-Side Auth Components (app/sign-in/[[...sign-in]]/page.tsx):**
```typescript
'use client';

import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <SignIn />
    </div>
  );
}
```

**Protected Route Pattern (client-side only):**
```typescript
'use client';

import { useAuth } from '@clerk/nextjs';
import { redirect } from 'next/navigation';

export default function DashboardPage() {
  const { userId, isLoaded } = useAuth();

  if (!isLoaded) {
    return <div>Loading...</div>;
  }

  if (!userId) {
    redirect('/sign-in');
  }

  return <div>Dashboard content</div>;
}
```

**JWT Token for API Calls:**
```typescript
'use client';

import { useAuth } from '@clerk/nextjs';

export default function JobSubmitter() {
  const { getToken } = useAuth();

  const submitJob = async () => {
    const token = await getToken();

    const response = await fetch('http://localhost:8000/jobs', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ /* job data */ }),
    });

    return response.json();
  };

  return <button onClick={submitJob}>Submit Job</button>;
}
```

**Security Limitation:**
Client-side protection cannot prevent viewing page HTML source or prevent JavaScript-disabled access. **All sensitive data MUST live on the backend API** (already implemented in Task 1.3), not in static HTML or client-side state.

**Sources:**
- https://clerk.com/docs/guides/development/upgrading/upgrade-guides/core-2/nextjs
- https://clerk.com/docs/getting-started/quickstart
- https://community.vercel.com/t/issue-with-clerk-authentication-and-next-js-static-and-dynamic-export-configuration/1642
- https://clerk.com/docs/reference/hooks/use-auth

---

### Tailwind CSS v3 Integration

**Version:** `tailwindcss@^3.4.0` (latest v3.x)

**Installation:**
```bash
npm install -D tailwindcss@^3 postcss autoprefixer
npx tailwindcss init -p
```

This creates `tailwind.config.js` and `postcss.config.js`.

**tailwind.config.js Configuration:**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Pharmaceutical compliance color palette
      colors: {
        'pharma-blue': {
          50: '#EBF8FF',
          100: '#D1EAFE',
          500: '#0066CC',
          600: '#1E3A8A',
        },
        'compliance': {
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          neutral: '#6B7280',
        },
      },
    },
  },
  plugins: [],
}
```

**Critical Content Path:** Must include `'./app/**/*.{js,ts,jsx,tsx,mdx}'` for App Router support. Omitting this causes Tailwind to miss classes in app directory components.

**app/globals.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Pharmaceutical compliance overrides */
@layer base {
  body {
    @apply text-gray-900 bg-gray-50;
  }
}
```

**Import in app/layout.tsx:**
```typescript
import './globals.css';
```

**Known Issues:**
- Scanning `node_modules` in content paths dramatically slows builds (avoid wildcards)
- Turbopack (default in Next.js 14) fully supports Tailwind v3
- No compatibility issues between Tailwind v3 and Next.js 14.2+

**Sources:**
- https://nextjs.org/docs/app/guides/tailwind-v3-css
- https://tailwindcss.com/docs/guides/nextjs

---

### TypeScript Configuration Best Practices

**Version:** `typescript@^5.6.0` (latest TypeScript 5.x)

**Recommended tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2021",
    "lib": ["dom", "dom.iterable", "esnext"],
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "esModuleInterop": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "incremental": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"],
      "@components/*": ["components/*"],
      "@lib/*": ["lib/*"]
    },
    "plugins": [
      {
        "name": "next"
      }
    ]
  },
  "include": [
    "next-env.d.ts",
    ".next/types/**/*.ts",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": ["node_modules"]
}
```

**Key Settings:**
- `strict: true` - Enables all strict type-checking (required for pharmaceutical compliance code quality)
- `moduleResolution: "bundler"` - Better ESM support with App Router
- `noEmit: true` - Next.js handles compilation
- `paths` - Path aliases for cleaner imports (`@components/Button` vs `../../components/Button`)

**Path Alias Setup:**
Create-next-app prompts for path alias configuration. Default is `@/*` mapping to project root.

**Sources:**
- https://bishtbytes.com/article/recommended-tsconfig-settings-for-nextjs-14/
- https://nextjs.org/docs/pages/api-reference/config/typescript

---

### ESLint + Prettier Configuration

**Required Packages:**
```json
{
  "devDependencies": {
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.33",
    "eslint-config-prettier": "^9.1.0",
    "prettier": "^3.3.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0"
  }
}
```

**.eslintrc.json:**
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "plugins": ["@typescript-eslint"],
  "parser": "@typescript-eslint/parser",
  "parserOptions": {
    "project": "./tsconfig.json"
  }
}
```

**Critical:** `"prettier"` MUST be last in `extends` array to disable ESLint formatting rules that conflict with Prettier.

**.prettierrc:**
```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "printWidth": 80
}
```

**package.json scripts:**
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "format": "prettier --write \"**/*.{js,jsx,ts,tsx,json,css,md}\""
  }
}
```

**Sources:**
- https://nextjs.org/docs/app/api-reference/config/eslint
- https://m4xshen.dev/posts/setup-nextjs-with-airbnb-eslint-prettier-typescript-and-tailwindcss

---

### Pharmaceutical Compliance UI/UX Patterns

**Color Palette (WCAG 2.1 AA Compliant):**

| Use Case | Color | Hex Code | Contrast Ratio (on white) |
|----------|-------|----------|---------------------------|
| Primary (trust/authority) | Blue | #0066CC | 8.59:1 |
| Success (approved jobs) | Green | #10B981 | 5.87:1 |
| Warning (pending review) | Amber | #F59E0B | 6.76:1 |
| Error (failed validation) | Red | #EF4444 | 5.29:1 |
| Neutral (disabled/archived) | Gray | #6B7280 | 5.74:1 |
| Background | Off-white | #F8F9FA | - |

**Typography:**
- **Base font size:** 14px-16px for data tables and body text
- **Typeface:** System fonts (Inter, Segoe UI) or IBM Plex Sans for professional appearance
- **Headings:**
  - H1: 24px, 600 weight (dashboard title)
  - H2: 18px, 600 weight (section headers)
  - H3: 14px, 600 weight (subsections)
- **Line height:** 1.5 for body text, 1.2 for headings
- **Letter spacing:** +0.3px to +0.5px for technical terms/abbreviations

**Layout Patterns:**
- **12-column grid** system (Tailwind default)
- **Generous white space** conveys professionalism (24px card padding)
- **Clean lines, flat design** (no gradients, minimal shadows)
- **Institutional color palette only** (blues, grays - avoid playful colors)

**Job Status Indicators (must combine color + icon + text):**
```typescript
const statusConfig = {
  submitted: {
    color: 'bg-blue-100 text-blue-800',
    icon: '✓',
    label: 'Submitted'
  },
  processing: {
    color: 'bg-amber-100 text-amber-800',
    icon: '⟳',
    label: 'Processing'
  },
  completed: {
    color: 'bg-green-100 text-green-800',
    icon: '✓',
    label: 'Completed'
  },
  failed: {
    color: 'bg-red-100 text-red-800',
    icon: '✕',
    label: 'Failed'
  },
};
```

**Accessibility Requirements (WCAG 2.1 AA):**
- Minimum 4.5:1 contrast ratio for normal text
- Minimum 3:1 for large text (18pt+) and interactive elements
- Keyboard navigation (tab order, focus indicators with 3:1 contrast)
- ARIA labels on all icons (`aria-label="Job submitted successfully"`)
- Semantic HTML (`<button>`, `<nav>`, `<main>`, `<table>`)
- Screen reader support (`role="status"`, `aria-live="polite"`)

**Dashboard Component Structure:**
```
┌─────────────────────────────────────────────┐
│ Header (nav, user menu, system status)      │
├─────────────────────────────────────────────┤
│ ┌──────┬──────────────────────────────┐    │
│ │Side- │ Main Content                 │    │
│ │bar   │ ┌──────────────────────────┐ │    │
│ │      │ │ Job Submission Form      │ │    │
│ │      │ └──────────────────────────┘ │    │
│ │      │ ┌──────────────────────────┐ │    │
│ │      │ │ Job Status Table         │ │    │
│ │      │ └──────────────────────────┘ │    │
│ └──────┴──────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**Sources:**
- https://www.koruux.com/50-examples-of-healthcare-UI/
- https://uxplanet.org/designing-medical-data-dashboards-ux-patterns-benchmarking-f83426ed6c07

---

### Environment Variable Handling in Static Exports

**CRITICAL GOTCHA: Build-Time vs Runtime**

In static exports, all `NEXT_PUBLIC_` prefixed variables are **inlined into the JavaScript bundle at build time**. This creates specific challenges:

**Build-Time Embedding:**
```javascript
// During build, this:
console.log(process.env.NEXT_PUBLIC_API_URL);

// Becomes this in output bundle:
console.log("http://localhost:8000");
```

**Docker Deployment Problem:**
A single Docker image built with `NEXT_PUBLIC_API_URL=http://localhost:8000` cannot be promoted to production with a different API URL because the value is frozen in the static bundle. Each environment requires a separate build.

**Solution for Multi-Environment Deployments:**
1. Build separate Docker images per environment (dev, staging, prod)
2. Use runtime configuration endpoint (requires external server)
3. Use client-side feature flag service (LaunchDarkly, Optimizely)

**Recommended Environment Variables:**
```
# .env.local (DO NOT COMMIT - add to .gitignore)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Usage in Code:**
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const response = await fetch(`${API_BASE_URL}/jobs`, {
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

**Sources:**
- https://nextjs.org/docs/pages/guides/environment-variables
- https://github.com/vercel/next.js/discussions/17641

---

### .gitignore Patterns for Next.js Projects

**Recommended .gitignore:**
```
# Next.js build output
.next/
out/

# Node dependencies
node_modules/

# Environment variables (CRITICAL: never commit)
.env
.env*.local
.env.local
.env.development.local
.env.production.local

# Testing
coverage/
.nyc_output/

# Log files
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# OS files
.DS_Store
Thumbs.db

# Editor directories
.vscode/
.idea/
*.swp
*.swo
*~

# TypeScript
*.tsbuildinfo
next-env.d.ts
```

**Critical:** `.env.local` and all `.env*.local` files MUST be in `.gitignore` to prevent credential leakage (Clerk secret keys).

**Sources:**
- https://blog.emb.global/next-js-gitignore/
- https://piterjov.hashnode.dev/effective-git-ignore-for-react-and-nextjs-applications

---

### Windows-Specific Development Considerations

**Performance Issue: Antivirus Interference**

Next.js development server on Windows can exhibit severe performance degradation (5-15 second page navigation delays) due to antivirus software scanning `.next/` directory on every file change.

**Solution: Add Project to Antivirus Exclusions**

**Windows Defender:**
1. Open Windows Security
2. Navigate to Virus & threat protection > Manage settings
3. Select "Add or remove exclusions"
4. Add folder exclusion: `C:\Users\anteb\Desktop\Courses\Projects\thesis_project`

**Performance Improvements:**
- Turbopack (default in Next.js 14 dev) provides 96.3% faster hot reload vs webpack
- Tailwind content paths: Avoid scanning `node_modules` (use specific paths only)
- Node.js 18.17+ required (Node.js 16 EOL)

**Sources:**
- https://nextjs.org/docs/app/guides/local-development
- https://github.com/vercel/next.js/discussions/67198

---

### Implementation Gotchas

**1. Static Export + Clerk Middleware Incompatibility**
- **Issue:** `clerkMiddleware()` requires Node.js runtime (not available in static exports)
- **Solution:** Use client-side auth only (`useAuth()`, `<SignIn />`) + backend JWT validation

**2. NEXT_PUBLIC_ Variables Are Build-Time Only**
- **Issue:** Cannot change environment variables in Docker at runtime
- **Solution:** Build separate images per environment OR use external runtime config service

**3. Image Optimization Disabled**
- **Issue:** `next/image` requires `images: { unoptimized: true }` with static export
- **Solution:** Accept unoptimized images OR use custom loader (Cloudinary, Imgix)

**4. Dynamic Routes Require generateStaticParams**
- **Issue:** Dynamic routes `[id]` won't build without `generateStaticParams`
- **Solution:** Implement `generateStaticParams` to enumerate all possible IDs

**5. Protected Routes Are Client-Side Only**
- **Issue:** Route protection via `useAuth()` cannot prevent HTML source viewing
- **Solution:** Store ALL sensitive data on backend API (already done in Task 1.3), never in static HTML

**6. Environment Variable Prefix**
- **Issue:** Forgetting `NEXT_PUBLIC_` prefix makes variables undefined in browser
- **Solution:** Always prefix browser-accessible variables with `NEXT_PUBLIC_`

**7. Tailwind Content Path for App Directory**
- **Issue:** Missing `./app/**/*.{js,ts,jsx,tsx,mdx}` in content paths breaks styling
- **Solution:** Explicitly include app directory in tailwind.config.js

**8. Windows Development Performance**
- **Issue:** Antivirus scanning causes 5-15s dev server delays
- **Solution:** Add project folder to antivirus exclusions

---

## Recommended Approach

### Step-by-Step Implementation Strategy

**Phase 1: Project Scaffolding (5 minutes)**
1. Run `npx create-next-app@latest main/frontend --typescript --tailwind --app --eslint`
2. Choose recommended defaults when prompted
3. Verify directory structure created: `main/frontend/app`, `main/frontend/public`

**Phase 2: Static Export Configuration (5 minutes)**
1. Modify `next.config.mjs`:
   - Add `output: 'export'`
   - Add `trailingSlash: true`
   - Add `images: { unoptimized: true }`
2. Update `tailwind.config.js`:
   - Verify `./app/**/*.{js,ts,jsx,tsx,mdx}` in content paths
   - Add pharmaceutical color palette to theme.extend.colors
3. Create `app/globals.css` with Tailwind directives
4. Test build: `npm run build` (should generate `out/` directory)

**Phase 3: Clerk Integration (10 minutes)**
1. Install Clerk: `npm install @clerk/nextjs@^5.0.0`
2. Wrap root layout with `<ClerkProvider>` in `app/layout.tsx`
3. Create sign-in page: `app/sign-in/[[...sign-in]]/page.tsx` with `<SignIn />`
4. Create sign-up page: `app/sign-up/[[...sign-up]]/page.tsx` with `<SignUp />`
5. Verify `.env.local` has `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
6. Test authentication flow: `npm run dev`, navigate to `/sign-in`

**Phase 4: Base Layout and Navigation (10 minutes)**
1. Create header component: `components/Header.tsx` with navigation
2. Add Clerk user menu: `<SignedIn>`, `<SignedOut>`, `<UserButton />`
3. Implement responsive layout with Tailwind
4. Add pharmaceutical color scheme to components
5. Test navigation: Dashboard, Jobs, Sign In/Out

**Phase 5: Linting and Formatting (5 minutes)**
1. Install Prettier: `npm install -D prettier eslint-config-prettier`
2. Create `.prettierrc` with formatting rules
3. Update `.eslintrc.json`: Add `"prettier"` to extends array (LAST)
4. Add format script to `package.json`: `"format": "prettier --write \"**/*.{ts,tsx,json,css,md}\""`
5. Run `npm run lint` and `npm run format`

**Phase 6: Environment Variables Setup (5 minutes)**
1. Create `.env.local` (if not exists) with:
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (from Task 1.4)
   - `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
2. Verify `.env.local` in `.gitignore`
3. Create `.env.example` (template without secrets) for documentation

**Phase 7: Compliance Branding (10 minutes)**
1. Update `app/layout.tsx` metadata (title, description)
2. Apply pharmaceutical color palette to global styles
3. Create professional typography scale (14-24px)
4. Implement WCAG-compliant focus indicators (3:1 contrast, 2px outline)
5. Add ARIA labels to navigation and interactive elements

**Phase 8: Testing and Validation (10 minutes)**
1. Run `npm run build` - verify static export completes
2. Serve static export: `npx serve out` - test in browser
3. Run `npm run lint` - verify no errors
4. Test authentication flow (sign in, sign up, user menu)
5. Test keyboard navigation (tab order, focus indicators)
6. Verify environment variables read correctly
7. Test Windows antivirus exclusion (if on Windows)

**Total Estimated Time:** 60 minutes

---

## Required Packages/Versions

```json
{
  "dependencies": {
    "next": "14.2.33",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "@clerk/nextjs": "^5.0.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "@types/node": "^20.11.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.57.0",
    "eslint-config-next": "14.2.33",
    "eslint-config-prettier": "^9.1.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "prettier": "^3.3.0"
  }
}
```

**Rationale:**
- `next@14.2.33` - Latest stable Next.js 14.2 with Turbopack and static export support
- `react@18.3.1` - Latest React 18 with concurrent features
- `@clerk/nextjs@^5.0.0` - Core 2 stable release (v6 has async breaking changes)
- `typescript@^5.6.0` - Latest TypeScript 5.x with improved type inference
- `tailwindcss@^3.4.0` - Latest Tailwind v3 with App Router support
- `eslint-config-prettier@^9.1.0` - Prevents ESLint/Prettier conflicts
- All `@types/*` packages match runtime versions for type safety

**Node.js Requirement:** 18.17.0+ (Node.js 16 EOL)

---

## Next Agent Guidance

### For task-executor

**Critical Architecture Decisions:**

1. **Static Export is NON-NEGOTIABLE** per task requirements (S3 hosting target)
2. **Clerk Authentication Pattern:** Use CLIENT-SIDE ONLY authentication
   - NO middleware (`clerkMiddleware()` will not work)
   - YES client components (`<SignIn />`, `useAuth()`)
   - Backend JWT validation already implemented in Task 1.4
3. **Environment Variables:** Use `NEXT_PUBLIC_` prefix for ALL browser-accessible variables
4. **Image Optimization:** MUST set `images: { unoptimized: true }` in next.config.mjs

**Implementation Checklist:**

- [ ] Run `npx create-next-app@latest main/frontend --typescript --tailwind --app --eslint`
- [ ] Modify `next.config.mjs`: Add `output: 'export'`, `trailingSlash: true`, `images.unoptimized: true`
- [ ] Install Clerk: `npm install @clerk/nextjs@^5.0.0`
- [ ] Wrap root layout with `<ClerkProvider>` in `app/layout.tsx`
- [ ] Import `app/globals.css` in root layout
- [ ] Create sign-in page: `app/sign-in/[[...sign-in]]/page.tsx`
- [ ] Create sign-up page: `app/sign-up/[[...sign-up]]/page.tsx`
- [ ] Update `tailwind.config.js`: Add pharmaceutical color palette, verify app directory in content paths
- [ ] Create `.prettierrc` and update `.eslintrc.json` (add "prettier" to extends)
- [ ] Verify `.env.local` has `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `NEXT_PUBLIC_API_BASE_URL`
- [ ] Add `.env.local` to `.gitignore`
- [ ] Add pharmaceutical branding (professional blue palette, clean typography)
- [ ] Implement WCAG 2.1 AA compliance (4.5:1 contrast, ARIA labels, keyboard navigation)
- [ ] Test build: `npm run build` (should generate `out/` directory without errors)
- [ ] Test static export: `npx serve out`
- [ ] Run linting: `npm run lint`

**Common Pitfalls to Avoid:**

1. **DO NOT** implement `clerkMiddleware()` - it will not work in static export
2. **DO NOT** forget `NEXT_PUBLIC_` prefix on environment variables
3. **DO NOT** use `getServerSideProps` or Server Actions (incompatible with static export)
4. **DO NOT** commit `.env.local` to Git
5. **DO NOT** forget `images: { unoptimized: true }` (build will fail)
6. **DO NOT** scan `node_modules` in Tailwind content paths (performance issue)
7. **DO NOT** skip Windows antivirus exclusions if developing on Windows

**Expected File Structure:**
```
main/frontend/
├── app/
│   ├── layout.tsx          # Root layout with ClerkProvider
│   ├── page.tsx            # Homepage
│   ├── globals.css         # Tailwind directives + pharmaceutical overrides
│   ├── sign-in/
│   │   └── [[...sign-in]]/
│   │       └── page.tsx    # Clerk SignIn component
│   └── sign-up/
│       └── [[...sign-up]]/
│           └── page.tsx    # Clerk SignUp component
├── components/
│   └── Header.tsx          # Navigation header with user menu
├── public/                 # Static assets
├── .env.local              # Environment variables (NOT committed)
├── .env.example            # Template (committed)
├── .gitignore              # Must include .env.local
├── next.config.mjs         # Static export config
├── tailwind.config.js      # Pharmaceutical color palette
├── tsconfig.json           # TypeScript strict mode
├── .eslintrc.json          # ESLint + Prettier config
├── .prettierrc             # Prettier formatting rules
└── package.json            # All dependencies listed above
```

**Testing Verification:**
- `npm run build` succeeds and generates `out/` directory
- `npx serve out` serves static site on http://localhost:3000
- Sign-in flow works (redirects to Clerk, returns to app)
- User menu displays after authentication
- `npm run lint` passes with 0 errors
- `npm run format` formats all files consistently
- Keyboard navigation works (tab through interactive elements)
- Focus indicators visible with 3:1 contrast ratio

**Integration with Existing Backend:**
- Frontend will call `http://localhost:8000/jobs` (FastAPI endpoint from Task 1.3)
- JWT token from `getToken()` passed in `Authorization: Bearer {token}` header
- Backend validates JWT using Clerk public keys (already implemented in Task 1.4)
- NO server-side rendering or middleware required

**GAMP-5 Compliance Notes:**
- Static export produces auditable build artifacts (`out/` directory)
- All source code tracked in Git for traceability
- Environment variables documented in `.env.example`
- Linting enforces code quality standards
- Accessibility compliance (WCAG 2.1 AA) supports regulatory audits

---

## Files Referenced

### Official Documentation
- https://nextjs.org/docs/app/guides/static-exports - Static export configuration
- https://nextjs.org/docs/app/api-reference/cli/create-next-app - create-next-app CLI
- https://nextjs.org/blog/next-14-2 - Next.js 14.2 release notes
- https://clerk.com/docs/getting-started/quickstart - Clerk Next.js quickstart
- https://clerk.com/docs/guides/development/upgrading/upgrade-guides/core-2/nextjs - Clerk Core 2 upgrade guide
- https://clerk.com/docs/reference/hooks/use-auth - useAuth() hook documentation
- https://tailwindcss.com/docs/guides/nextjs - Tailwind CSS Next.js integration
- https://nextjs.org/docs/pages/guides/environment-variables - Environment variables guide

### Community Resources
- https://community.vercel.com/t/issue-with-clerk-authentication-and-next-js-static-and-dynamic-export-configuration/1642 - Static export + Clerk discussion
- https://github.com/vercel/next.js/discussions/17641 - Docker + NEXT_PUBLIC_ environment variables
- https://github.com/vercel/next.js/discussions/67198 - Windows performance issues
- https://blog.emb.global/next-js-gitignore/ - Next.js .gitignore patterns

### Design References
- https://www.koruux.com/50-examples-of-healthcare-UI/ - Healthcare UI patterns
- https://uxplanet.org/designing-medical-data-dashboards-ux-patterns-benchmarking-f83426ed6c07 - Medical dashboard UX

### Technical References
- https://bishtbytes.com/article/recommended-tsconfig-settings-for-nextjs-14/ - TypeScript configuration
- https://m4xshen.dev/posts/setup-nextjs-with-airbnb-eslint-prettier-typescript-and-tailwindcss - ESLint + Prettier setup
- https://nextjs.org/docs/app/guides/local-development - Local development performance

### GitHub Documentation
- https://github.com/vercel/next.js/blob/canary/docs/01-app/02-guides/static-exports.mdx - Static export source code
- https://github.com/vercel/next.js/blob/canary/docs/01-app/03-api-reference/05-config/01-next-config-js/trailingSlash.mdx - trailingSlash configuration
