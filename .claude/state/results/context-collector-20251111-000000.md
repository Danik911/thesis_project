# Context Collector Result - 2025-11-11T00:00:00Z

## Agent Configuration
- Agent: context-collector
- Task ID: 2.4
- Invoked: 2025-11-11T00:00:00Z
- Duration: 45 minutes
- Status: SUCCESS

## Task Understanding

Task 2.4 requires hardening the Next.js frontend for accessibility and pharmaceutical compliance by:
1. Auditing existing frontend components against WCAG 2.1 AA standards
2. Integrating automated accessibility checks (axe-core) into the development workflow
3. Documenting manual accessibility testing scenarios for GAMP-5 compliance records

This task builds on Task 2.1 (Next.js Pages Router setup), Task 2.2 (Clerk authentication), and Task 2.3 (LangFuse dashboard), ensuring the pharmaceutical test generation system meets regulatory accessibility requirements.

---

## Research Findings

### WCAG 2.1 AA Requirements

#### Core Success Criteria for Pharmaceutical Dashboards

**1. Color Contrast (SC 1.4.3 - Contrast Minimum)**
- Normal text: 4.5:1 minimum contrast ratio
- Large text (18pt+/14pt bold+): 3:1 minimum contrast ratio
- UI components (SC 1.4.11 - Non-text Contrast): 3:1 minimum contrast ratio
- Critical for pharmaceutical applications where color-coded medication status or clinical severity might be used
- Pharmaceutical blue/green color schemes require careful luminance planning
- Color alone cannot be the sole visual means of conveying information (must have text, icons, or patterns)

**2. Keyboard Accessibility (SC 2.1.1 - Keyboard)**
- All functionality must be operable through keyboard without specific timings
- Critical for healthcare professionals who may have motor disabilities or use voice control
- Includes: forms, navigation menus, data tables, dashboard filters, authentication flows
- Exception: functionality requiring path-based movement (e.g., freehand drawing) - NOT applicable to pharmaceutical dashboards

**3. Focus Management (SC 2.4.3 - Focus Order & SC 2.4.7 - Focus Visible)**
- Focusable components must receive focus in logical order preserving meaning
- Visible keyboard focus indicator required at all times
- Critical challenge in Next.js Pages Router SPAs: focus management on route changes
- Must programmatically move focus to main heading (h1/h2 with tabindex="-1") when content changes

**4. Bypass Blocks (SC 2.4.1 - Bypass Blocks)**
- Skip links required to bypass repeated navigation blocks
- "Skip to main content" link at beginning of page
- ARIA landmarks provide complementary approach (role="navigation", role="main", role="search")
- Screen readers can jump between landmarks using keyboard shortcuts

**5. Form Accessibility (SC 3.3.1 - Error Identification & SC 3.3.2 - Labels or Instructions)**
- Input errors must be identified and described in text
- Labels or instructions required for all user input
- Error messages must use aria-describedby to associate with fields
- aria-invalid="true" required on fields with validation errors
- Critical for pharmaceutical forms (DEA numbers, medication names, clinical trial data)

**6. Dynamic Content (SC 4.1.3 - Status Messages)**
- Status messages must be programmatically determinable
- ARIA live regions required for dynamic updates (SWR data fetching, loading states, errors)
- aria-live="polite" for non-critical updates (data refreshed, items added)
- aria-live="assertive" for urgent updates (drug interaction warnings, critical errors)
- aria-busy="true" during loading, then "false" when complete

**7. Name, Role, Value (SC 4.1.2)**
- All UI components must have programmatically determinable name, role, state, and value
- Critical for Clerk authentication components (UserButton, SignIn, SignUp)
- Custom buttons created with div elements need role="button", tabIndex="0", keyboard handlers, aria-pressed state

**8. Tables and Data Presentation (SC 1.3.1 - Info and Relationships)**
- Table structure must be programmatically determinable
- th elements with scope="col" or scope="row" required
- caption elements for table titles
- Critical for pharmaceutical data grids (medication inventory, clinical trial results, laboratory values)

#### Pharmaceutical-Specific Considerations

- FDA Section 508 compliance aligns with WCAG 2.0 (WCAG 2.1 provides improved accessibility)
- Pharmaceutical applications handling sensitive health information require accessible authentication
- Clinical environments may have suboptimal lighting, multitasking healthcare professionals
- Accessibility features critical for patient safety and clinical accuracy (medication information, dosage tables, lab values)

### Axe-Core Integration for Next.js Pages Router

#### Package Selection
- **@axe-core/react**: Runtime testing within React application (development only)
- **@axe-core/playwright**: E2E testing outside application context (CI/CD)
- **Version compatibility**: Compatible with Next.js 14.2.33 and React 18

#### Installation
```bash
npm install --save-dev @axe-core/react
npm install --save-dev react-dom  # if not already present
```

#### Pages Router Implementation

**1. Create utility function (utils/reportAccessibility.ts)**
```typescript
import type React from 'react'

export const reportAccessibility = async (
  App: typeof React,
  config?: Record<string, unknown>
): Promise<void> => {
  if (
    typeof window !== 'undefined' &&
    process.env.NODE_ENV !== 'production'
  ) {
    const axe = await import('@axe-core/react')
    const ReactDOM = await import('react-dom')
    axe.default(App, ReactDOM, 1000, config)
  }
}

export default reportAccessibility
```

**2. Integrate into pages/_app.tsx**
```typescript
import React from 'react'
import reportAccessibility from '../utils/reportAccessibility'
import type { AppProps } from 'next/app'

function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />
}

reportAccessibility(React)

export default MyApp
```

**Key Configuration Details:**
- `typeof window !== 'undefined'`: Client-side only (prevents SSR errors)
- `process.env.NODE_ENV !== 'production'`: Development-only (not bundled in production)
- Dynamic imports: Loaded only when needed during development
- Output: Browser DevTools console with severity, code snippets, detailed explanations

#### Limitations
- Development-time runtime testing only (not for CI/CD)
- Does not test built Next.js pages (.next/server)
- Automated testing catches ~80% of issues (manual testing required for remaining 20%)
- Cannot validate pharmaceutical-specific compliance requirements (requires domain expertise)

### GAMP-5 UI Expectations

#### Category 5 Configured Software UI Validation

**1. User Requirements and Traceability**
- UI elements must be included in User Requirements Specifications (URS)
- Functional and design specifications required
- Traceability matrix linking UI controls to requirements
- Risk and impact assessments for UI controls
- Extensive verification testing documenting UI performance

**2. User Interface Design Requirements**
- Support accuracy, data integrity, and ease of use
- Prevent user errors through design
- Reflect clear separation of duties per URS
- Facilitate proper entry, review, and approval of records
- Secondary review mechanisms where required by regulations

**3. Audit Trail Visualization**
- UI must enable viewing audit trails with appropriate permissions
- Display: who made changes, what was changed, when it occurred
- Compliant with 21 CFR Part 11 and EU Annex 11
- Changes clearly attributed to specific users (full name, unique identifier, timestamp)
- Design must prevent alteration or hiding of audit trail records

**4. Form Validation and Error Handling**
- All user input must be form validated (controlled vocabulary, range checks, required fields, logical consistency)
- Clear, descriptive, and immediate error feedback to users
- Corrections must occur before data submission
- Error messages themselves validated per functional specifications

**5. Data Presentation Standards**
- Maintain legibility, accuracy, and traceability
- Appropriate date/time formats, SI units, significant figures per SOPs
- Tables, charts, records avoid ambiguity
- Prevent confusion between drafts, originals, and voided records

**6. User Identification Display**
- Display unique identifier (username or electronic signature per 21 CFR Part 11)
- Display full name of user performing regulated actions
- For two-person review: both users' identities displayed and logged

**7. ALCOA+ Principles in UI Design**
- **Attributable**: Every entry/action shows who performed it
- **Legible**: Information and records easily readable on-screen
- **Contemporaneous**: Time-stamping actions at time of operation
- **Original**: UI supports access to true original record (not just copies)
- **Accurate**: Clear, unambiguous display; error prevention and validation
- **Complete**: UI makes record deletion/obscuring impossible
- **Consistent**: Versioning clearly visualized and traceable
- **Enduring**: Facilitate retrieval and review for GxP-mandated lifetime
- **Available**: Records accessible for audit review

**8. 21 CFR Part 11 Electronic Signature UI Requirements**
- Electronic signatures uniquely attributable to single individual
- Two distinct identification components (username/password, biometric)
- Displayed alongside associated records and actions
- Signature manifestation (signer, date/time, purpose) wherever record is signed

**9. Validation Documentation**
- Screenshots of UI workflows
- UI workflow descriptions
- Evidence of testing for all validation-relevant UI features
- Manual accessibility testing outcomes for compliance records

### eslint-plugin-jsx-a11y Configuration

#### Installation and Setup
```bash
npm install --save-dev eslint-plugin-jsx-a11y
```

#### Flat Config (eslint.config.js/eslint.config.mjs)
```js
import jsxA11y from 'eslint-plugin-jsx-a11y';
export default [
  jsxA11y.flatConfigs.recommended,
  // or for strict: jsxA11y.flatConfigs.strict
  {
    settings: {
      'jsx-a11y': {
        components: {
          UserButton: 'button',
          SignIn: 'form',
          SignUp: 'form'
        }
      }
    }
  }
];
```

#### Legacy Config (.eslintrc.json)
```json
{
  "extends": ["plugin:jsx-a11y/recommended"],
  "settings": {
    "jsx-a11y": {
      "components": {
        "UserButton": "button",
        "SignIn": "form",
        "SignUp": "form"
      }
    }
  },
  "rules": {
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/aria-live": "error",
    "jsx-a11y/tabindex-no-positive": "error"
  }
}
```

#### Ruleset Recommendations
- **Recommended**: Balanced rules, fewer false positives (recommended for most apps)
- **Strict**: More comprehensive, can be noisy for dynamic dashboards
- Pharmaceutical applications should use **recommended** with selective strict rules

#### Integration with next lint
- Next.js includes eslint-config-next which surfaces jsx-a11y errors by default
- Custom configs must explicitly include plugin:jsx-a11y/recommended
- Run via: `npm run lint`

#### Common Violations Caught
- img elements missing alt text (jsx-a11y/alt-text)
- Non-interactive elements with click handlers (jsx-a11y/no-static-element-interactions)
- Form fields without associated labels (jsx-a11y/label-has-associated-control)
- Table markup issues (missing th, scope, caption)
- Improper ARIA attributes (jsx-a11y/aria-*)
- Positive tabIndex values (jsx-a11y/tabindex-no-positive)
- Autofocus on form fields (jsx-a11y/no-autofocus)

#### Clerk Component Mapping
Map Clerk components to semantic roles to enable proper linting:
```json
{
  "settings": {
    "jsx-a11y": {
      "components": {
        "UserButton": "button",
        "SignIn": "form",
        "SignUp": "form"
      }
    }
  }
}
```

### Implementation Gotchas

#### 1. Clerk Authentication Components
**Issue**: Clerk components (UserButton, SignIn, SignUp) may render custom widgets using div/span without proper roles
**Fix**:
- Map components in ESLint settings
- Wrap in semantic roles where needed
- Add aria-label to dialogs/modals
- Test keyboard and screen reader compatibility

```jsx
// Good
<div role="dialog" aria-modal="true" aria-label="User account actions">
  <UserButton />
</div>

<SignIn formProps={{ 'aria-label': 'Sign In Form' }} />
```

#### 2. Next.js Link Focus States
**Issue**: Link components without visible focus (especially with Tailwind)
**Fix**: Always use focus-visible utilities

```jsx
// Bad
<Link href="/about" className="text-blue-500">About</Link>

// Good
<Link
  href="/about"
  className="text-blue-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
  aria-current={isActive ? "page" : undefined}
>
  About
</Link>
```

#### 3. Tailwind Focus Styles
**Issue**: Using `outline-none` without replacement visible focus indicator
**Fix**: Always replace with focus-visible utilities

```jsx
// Bad
<button className="outline-none">Submit</button>

// Good
<button className="focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600">
  Submit
</button>
```

**Rule**: NEVER entirely remove focus styling; always supply visible state for :focus-visible

#### 4. Client-Side Routing Focus Management
**Issue**: After navigation, focus does not move to main content (keyboard/screen reader users disoriented)
**Fix**: Programmatically move focus to main heading on route change

```jsx
// In layout or main render
useEffect(() => {
  document.getElementById('main')?.focus();
}, [router.pathname]);

// In JSX
<main id="main" tabIndex="-1">...</main>
```

#### 5. SWR Dynamic Content Loading
**Issue**: Silent updates - screen readers don't know content has changed
**Fix**: Use ARIA live regions

```jsx
// Bad
const { data } = useSWR('/api/user');
<p>{data?.username}</p>

// Good
<div aria-live="polite" aria-atomic="true">
  <p>{data?.username}</p>
</div>
```

#### 6. Table Accessibility
**Issue**: Tables lack semantic markup (th, scope, caption)
**Fix**: Use proper semantic elements

```jsx
// Good
<table className="w-full border border-gray-300">
  <caption className="text-lg font-semibold">User List</caption>
  <thead>
    <tr>
      <th scope="col" className="border px-2">Name</th>
      <th scope="col" className="border px-2">Email</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td className="border px-2">John Smith</td>
      <td className="border px-2">john@example.com</td>
    </tr>
  </tbody>
</table>
```

#### 7. Color Contrast with Tailwind
**Issue**: Default Tailwind pastel colors don't meet WCAG 4.5:1 minimum contrast
**Fix**: Use darker shades for text

```jsx
// Bad - insufficient contrast
<p className="text-gray-400">Low contrast text</p>

// Good - meets WCAG 2.1 AA
<p className="text-gray-800">Accessible text</p>
```

#### 8. Form Validation and Error Messages
**Issue**: Validation errors not announced, errors only in color
**Fix**: Use aria-live, aria-describedby, role="alert"

```jsx
// Good
<input
  id="email"
  name="email"
  aria-invalid={!!error}
  aria-describedby={error ? "email-error" : undefined}
/>
{error && (
  <span id="email-error" role="alert" className="text-red-700" aria-live="assertive">
    {error}
  </span>
)}
```

#### 9. Loading States and Skeleton Screens
**Issue**: Loading indicators not announced to screen readers
**Fix**: Wrap in role="status" with sr-only text

```jsx
// Good
{isLoading && (
  <div role="status" aria-live="polite">
    <Skeleton />
    <span className="sr-only">Loading content</span>
  </div>
)}
```

#### 10. Modal Dialogs and Focus Trapping
**Issue**: Modals lack role="dialog", focus not trapped
**Fix**: Use role="dialog", aria-modal="true", focus trap

```jsx
// Good
{showModal && (
  <div
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
    tabIndex="-1"
    ref={modalRef}
    className="fixed inset-0 bg-white p-4"
  >
    <h2 id="modal-title">Modal Dialog</h2>
    <button onClick={closeModal}>Close</button>
    {/* Focus trap logic: use focus-trap-react library */}
  </div>
)}
```

**Note**: Consider using focus-trap-react or @radix-ui/react-dialog for robust focus management

### Testing Strategies

#### Automated Testing (Development Environment)

**1. axe-core Runtime Testing**
- Run automatically in development via @axe-core/react
- Outputs violations to browser console
- Provides severity levels, code snippets, detailed explanations
- Catches ~80% of accessibility issues

**2. ESLint Static Analysis**
- Run via `npm run lint`
- Catches JSX accessibility issues during code review
- Integrates with IDE linters for real-time feedback
- Catches issues before runtime

#### Manual Testing Procedures

**1. Keyboard Navigation Testing**
- Test all interactive elements using only keyboard
- **Tab**: Move forward through focusable items
- **Shift+Tab**: Move backward
- **Enter/Space**: Activate buttons/links, toggle checkboxes
- **Arrow keys**: Navigate menus, dropdowns, radio groups, tables
- **Escape**: Close modals/dialogs
- **Test scenarios**:
  - Authenticate by completing login forms keyboard-only
  - Navigate dashboards (tab through metrics, charts)
  - Navigate data tables (all rows/cells reachable)
  - Open, use, and close modal dialogs
  - Ensure never "trapped" in any component
- **Expectation**: All functionality accessible without mouse, focus never lost, logical order

**2. Screen Reader Testing**
- **NVDA (Windows)**: Ctrl+Alt+N
- **JAWS (Windows)**: Insert+J
- **VoiceOver (Mac)**: Cmd+F5
- **Navigation shortcuts**:
  - H: Jump to headings
  - D: Jump to landmarks
  - T: Jump to tables
  - Tab/Shift+Tab: Focus navigation
- **Test scenarios**:
  - Login: Label announcements on fields/buttons
  - Dashboard: Headings, regions, landmarks announced
  - Data tables: Row/column headers, current cell value, sort state
  - Modals: Content announced on open, focus remains inside
  - ARIA live regions: Dynamic updates announced
- **Expectation**: No missing/incorrect labels, ARIA attributes properly announced, logical reading order

**3. Focus Visibility Testing**
- Tab through all interactive elements
- Visually confirm clear, visible focus indicator
- Test in normal AND high-contrast system settings
- Test in guest AND authenticated contexts
- **Expectation**: Visible focus at all times, not lost or hidden

**4. Color Contrast Testing**
- Use automated tools: axe DevTools, WAVE, Colour Contrast Analyser
- Manually verify in live UI:
  - Error/success feedback in forms
  - Dashboard widgets
  - Table headers and contents
- **WCAG 2.1 AA requirement**: 4.5:1 for text, 3:1 for large text
- **Expectation**: All text/content meets or exceeds required contrast

**5. ARIA Live Region Testing**
- Trigger dynamic updates (form validation, dashboard alerts)
- Verify aria-live regions implemented
- With screen reader running, confirm updates announced automatically
- **Pharmaceutical-specific**: Validation errors, real-time dashboard updates, system alerts
- **Expectation**: Important dynamic messaging announced correctly

#### Compliance Documentation Requirements

**Must Document:**
- Unique test case ID and description
- Steps taken (manual and assistive tech)
- Observed results (screenshots, screen reader transcripts)
- Pass/fail status for each WCAG 2.1 AA criterion
- Screenshots of focus indicators, error messages, modals, skip links, high-contrast views
- Screen capture videos or audio of screen reader announcements
- Summarized test report mapping components to WCAG 2.1 AA success criteria

**Format**: Create documentation files in `main/docs/compliance/accessibility/`
- `accessibility-test-plan.md`: Test scenarios and procedures
- `accessibility-test-results-YYYYMMDD.md`: Test execution results
- `wcag-2.1-aa-compliance-matrix.md`: Traceability matrix

**GAMP-5 Requirement**: Documentation must be sufficiently detailed to demonstrate conformance, allowing independently repeatable verification

### Recommended Approach

#### Phase 1: Audit Existing Components (Week 1)

**1. Install and Configure Tools**
```bash
# Install axe-core for runtime testing
npm install --save-dev @axe-core/react

# Verify eslint-plugin-jsx-a11y is included
npm list eslint-plugin-jsx-a11y
```

**2. Configure axe-core**
- Create `main/frontend/utils/reportAccessibility.ts`
- Integrate into `pages/_app.tsx`
- Test in development: `npm run dev` and check console

**3. Configure ESLint**
- Update ESLint config to use `plugin:jsx-a11y/recommended`
- Add Clerk component mappings
- Run `npm run lint` and document violations

**4. Audit Existing Components**
Manually review each component against common violations:
- **Layout.tsx**: Skip link, focus management, ARIA landmarks
- **Header.tsx**: Navigation keyboard accessibility, active page indication
- **dashboard.tsx**: Loading states, ARIA live regions, heading hierarchy
- **observability.tsx**: Table accessibility, chart descriptions, loading states
- **sign-in.tsx / sign-up.tsx**: Form labels, error handling, keyboard navigation

**5. Document Findings**
Create `main/docs/compliance/accessibility/audit-findings-YYYYMMDD.md` with:
- Component name
- WCAG 2.1 AA violations found
- Severity (critical, serious, moderate, minor)
- Recommended fix
- GAMP-5 impact assessment

#### Phase 2: Fix Critical Violations (Week 1-2)

**Priority Order:**
1. **Critical**: Keyboard navigation blockers, missing form labels, insufficient color contrast
2. **Serious**: Missing ARIA attributes, improper focus management, table accessibility
3. **Moderate**: Missing skip links, improper heading hierarchy, incomplete ARIA live regions
4. **Minor**: Optimization of ARIA usage, enhanced focus styles

**NO FALLBACK LOGIC**: All fixes must explicitly handle errors without masking failures

#### Phase 3: Document Manual Testing Procedures (Week 2)

**Create Test Documentation:**
- `main/docs/compliance/accessibility/manual-test-procedures.md`
  - Keyboard navigation test cases
  - Screen reader test scenarios (NVDA, JAWS, VoiceOver)
  - Focus visibility test procedures
  - Color contrast verification procedures
  - ARIA live region testing
  - Form validation testing
  - Table navigation testing
  - Modal dialog testing
  - Skip link testing

- `main/docs/compliance/accessibility/wcag-2.1-aa-compliance-matrix.md`
  - Traceability matrix mapping components to WCAG success criteria
  - Test case references
  - Pass/fail status
  - Evidence references (screenshots, recordings)

**GAMP-5 Alignment**: Documentation structure supports validation deliverables (Validation Plan, test documentation, traceability to regulatory requirements)

#### Phase 4: Validation Testing (Week 2)

**Execute Manual Tests:**
1. Keyboard navigation testing across all pages
2. Screen reader testing (minimum: NVDA on Windows)
3. Focus visibility verification
4. Color contrast verification (all text/UI components)
5. ARIA live region verification (SWR updates, error states)
6. Form accessibility verification
7. Table navigation verification
8. Modal dialog verification

**Document Results:**
- Create `main/docs/compliance/accessibility/test-results-YYYYMMDD.md`
- Include screenshots of successful tests
- Include screen reader output transcripts where applicable
- Record pass/fail for each WCAG 2.1 AA criterion tested
- Document any exceptions or known limitations

### Required Libraries/Versions

```json
{
  "devDependencies": {
    "@axe-core/react": "^4.10.2",
    "eslint-plugin-jsx-a11y": "^6.10.2"
  }
}
```

**Optional (for future CI/CD integration - NOT in this task scope):**
```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.10.2",
    "playwright": "^1.49.1",
    "pa11y-ci": "^3.2.0",
    "@lhci/cli": "^0.15.0"
  }
}
```

**Version Compatibility:**
- Next.js 14.2.33: ✅ Compatible
- React 18: ✅ Compatible
- Clerk v6.35.0: ✅ Compatible
- Tailwind CSS 3.4.1: ✅ Compatible

**Installation Method**: Use `uv add --dev {package}` (NOT npm install)

### Next Agent Guidance

**For task-executor:**

1. **Install Required Packages**
   ```bash
   uv add --dev @axe-core/react
   # eslint-plugin-jsx-a11y likely already installed with next/core-web-vitals
   ```

2. **Create Accessibility Utility**
   - File: `main/frontend/utils/reportAccessibility.ts`
   - Implement client-side-only, development-only axe-core integration
   - Use dynamic imports to avoid production bundle

3. **Update ESLint Configuration**
   - Add or verify `plugin:jsx-a11y/recommended` in extends
   - Add Clerk component mappings in settings
   - Run lint and document current violations (do NOT fix yet - document first)

4. **Audit Existing Components**
   - Review Layout.tsx, Header.tsx, dashboard.tsx, observability.tsx, sign-in.tsx, sign-up.tsx
   - Document violations against WCAG 2.1 AA requirements
   - Prioritize: Critical > Serious > Moderate > Minor
   - Create audit findings document: `main/docs/compliance/accessibility/audit-findings-YYYYMMDD.md`

5. **Fix Critical Violations**
   - Add skip link to Layout.tsx
   - Ensure all Links have focus-visible styles
   - Add ARIA live regions for SWR loading/error states
   - Fix table accessibility (scope attributes, caption)
   - Ensure form labels and error handling accessibility
   - Add ARIA landmarks (role="navigation", role="main", role="contentinfo")
   - Implement focus management for route changes

6. **Create Manual Test Documentation**
   - File: `main/docs/compliance/accessibility/manual-test-procedures.md`
   - Include keyboard navigation test cases
   - Include screen reader test scenarios
   - Include WCAG 2.1 AA compliance verification procedures
   - Align with GAMP-5 validation documentation requirements

7. **Create Compliance Matrix**
   - File: `main/docs/compliance/accessibility/wcag-2.1-aa-compliance-matrix.md`
   - Map each component to WCAG 2.1 AA success criteria
   - Reference test cases
   - Track pass/fail status
   - Include evidence references

8. **NO FALLBACK LOGIC**
   - All accessibility fixes must fail explicitly if something doesn't work
   - Error states must be accessible and informative
   - Never mask accessibility failures with default/fallback content

9. **Testing Requirements**
   - Run `npm run dev` and verify axe-core outputs violations to console
   - Run `npm run lint` and document all jsx-a11y violations
   - Manually test keyboard navigation across all pages
   - Manually test at least one screen reader (NVDA recommended)
   - Document all test results

10. **GAMP-5 Compliance**
    - All documentation must support validation deliverables
    - Traceability to regulatory requirements (WCAG 2.1 AA, 21 CFR Part 11)
    - Evidence of testing (screenshots, transcripts)
    - Audit trail of accessibility improvements

**Out of Scope (DO NOT IMPLEMENT):**
- CI/CD automation (GitHub Actions workflows)
- Playwright E2E testing
- Pa11y or Lighthouse CI integration
- Automated test report generation in CI

**Success Criteria:**
- ✅ axe-core integrated and reporting violations in development console
- ✅ eslint-plugin-jsx-a11y configured and running in lint command
- ✅ All critical WCAG 2.1 AA violations fixed
- ✅ Manual testing procedures documented
- ✅ WCAG 2.1 AA compliance matrix created
- ✅ Test results documented with evidence
- ✅ GAMP-5 validation documentation requirements met
- ✅ 0 NO FALLBACK LOGIC violations

## Files Referenced

### Documentation Sources
- WCAG 2.1 Web Content Accessibility Guidelines: https://www.w3.org/TR/WCAG21/
- WCAG 2.1 Understanding Documents: https://www.w3.org/WAI/WCAG21/Understanding/
- FDA Accessibility Guidance: https://www.fda.gov/about-fda/accessibility-fda/
- GAMP-5 Validation Framework: https://intuitionlabs.ai/pdfs/gamp-5-computerized-system-validation-in-pharma.pdf

### Implementation Guides
- axe-core Next.js Integration: https://larsmagnus.co/blog/how-to-test-for-accessibility-with-axe-core-in-next-js-and-react
- eslint-plugin-jsx-a11y Documentation: https://www.npmjs.com/package/eslint-plugin-jsx-a11y
- Next.js Accessibility Guide: https://nextjs.org/docs/architecture/accessibility
- Next.js Pages Router Focus Management: https://www.tpgi.com/client-side-routing-accessibility/
- ARIA Live Regions Guide: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions

### Testing Resources
- Manual Accessibility Testing Procedures: https://equalizedigital.com/accessibility-checker/how-to-manually-check-your-website-for-accessibility/
- Screen Reader Testing Guide: https://www.deque.com/wcag/testing/
- WCAG 2.1 AA Checklist: https://accessibe.com/blog/knowledgebase/wcag-checklist

### Pharmaceutical Compliance
- GAMP-5 Categories and Validation: https://www.ptc.com/en/blogs/alm/gamp-5-guide-categories-requirements-and-validation
- FDA CSA Guidance and GAMP-5 Alignment: https://www.valgenesis.com/blog/how-do-the-fdas-csa-guidance-and-gamp-5-align
- 21 CFR Part 11 Guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application
