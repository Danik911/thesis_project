# Current Task Context: 2.4

## Task File
PRPs/tasks/2.4-frontend-accessibility.md

## Task Content
# Task P2.4 – Harden Next.js Frontend Accessibility & Compliance

## What to Do
- Audit frontend components against WCAG 2.1 AA and GAMP-5 UI expectations.
- Integrate automated accessibility checks (e.g., axe-core) into CI.
- Document manual accessibility testing scenarios for compliance records.

## Dependencies
- Requires initial frontend layout (Task P2.1) and dashboard components (Task P2.3).

## Best Practices
- Use semantic HTML and ARIA attributes only when needed to avoid over-annotation.
- Provide textual descriptions for all observability charts and LLM outputs.
- Maintain audit trail of accessibility testing outcomes in compliance documentation.

## Code Example
```bash
# package.json scripts
"scripts": {
  "lint": "next lint",
  "test:a11y": "axe --exit zero .next/server/app"
}
```

## Links
- [Axe for Next.js](https://www.deque.com/blog/introducing-axe-core-testing-in-next-js/)
- [WCAG 2.1 Checklist](https://www.w3.org/TR/WCAG21/)

## Testing Strategy
- Run automated tests via `npm run test:a11y` and capture results in CI artifacts.
- Perform manual keyboard navigation test across primary workflows.
- Record screen reader walkthrough for compliance evidence.

## Common Issues to Avoid
- Treating color contrast as optional; enforce via design tokens.
- Forgetting to localize dynamic content for multilingual requirements.
- Skipping manual testing in favor of automated checks alone.

## Task Metadata
- Task ID: 2.4
- Phase: 2 - Backend Abstraction
- Started: 2025-11-11T00:00:00Z
- Workflow Status: INITIALIZED
