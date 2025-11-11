# Current Task Context: 2.1

## Task File
PRPs/tasks/2.1-nextjs-setup.md

## Task Content
# Task P2.1 – Initialize Next.js 14 Frontend Project

## What to Do
- Scaffold a Next.js App Router project (TypeScript, Tailwind) under `main/frontend` and configure static export (`output: 'export'`).
- Set up environment variable handling for Clerk publishable key and API base URL.
- Establish global styles, layout, and base navigation shell aligned with compliance branding.

## Dependencies
- Requires Clerk configuration (Task P1.4) to reuse publishable key.

## Best Practices
- Leverage the Next.js `app` directory for server components where possible to improve performance.
- Use `trailingSlash: true` to produce S3-friendly paths for static hosting.
- Commit linting/formatting configuration (ESLint, Prettier) to align with backend standards.

## Code Example
```ts
// next.config.mjs
const config = {
  output: 'export',
  trailingSlash: true,
  experimental: {
    typedRoutes: true
  }
};
export default config;
```

## Links
- [Next.js static export guide](https://nextjs.org/docs/app/guides/static-exports)

## Testing Strategy
- Run `npm run lint` and `npm run build` to ensure project compiles.
- Use `npx next export` (via `output: 'export'`) and serve the `out` directory locally to validate static output.
- Add smoke test verifying environment variables are read correctly via `next dev`.

## Common Issues to Avoid
- Forgetting to add `.env.local` to `.gitignore`, risking credential leakage.
- Not enabling `output: 'export'`, resulting in server-side code incompatible with S3 hosting.
- Neglecting to configure TypeScript path aliases consistent with backend shared models if needed.

## Task Metadata
- Task ID: 2.1
- Phase: 2 - Frontend Dashboard
- Started: 2025-11-11T00:00:00Z
- Workflow Status: INITIALIZED
