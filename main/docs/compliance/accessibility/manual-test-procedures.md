# Manual Accessibility Test Procedures

## Document Information
**Document ID:** ATP-A11Y-001
**Version:** 1.0
**Date:** 2025-11-11
**Status:** Active
**Author:** Task Executor Agent (task-executor)
**Purpose:** Define manual accessibility testing procedures for GAMP-5 validation and WCAG 2.1 AA compliance

## Scope
This document defines manual testing procedures for the Pharmaceutical Test Generation System frontend to verify:
- WCAG 2.1 AA compliance
- GAMP-5 UI validation requirements
- Pharmaceutical-specific accessibility considerations
- 21 CFR Part 11 UI requirements (when applicable)

## Prerequisites

### Test Environment
- **Browser:** Latest stable Chrome, Firefox, and Edge
- **Screen Reader:** NVDA 2024.1+ (Windows) or VoiceOver (Mac)
- **Operating System:** Windows 10/11 or macOS 13+
- **Test User:** Valid Clerk authentication credentials
- **Network:** Access to LangFuse Cloud (https://cloud.langfuse.com)

### Test Data
- Valid URS document for test generation (if testing observability)
- Multiple test users for multi-user scenarios
- Sample data in LangFuse for observability testing

### Skills Required
- Basic keyboard navigation proficiency
- Screen reader operation (NVDA/VoiceOver)
- Understanding of WCAG 2.1 AA success criteria
- Pharmaceutical regulatory compliance awareness

---

## Test Procedures

### TP-A11Y-001: Keyboard Navigation Test

**Objective:** Verify all functionality is accessible via keyboard without requiring mouse

**WCAG Criteria:** 2.1.1 Keyboard (Level A)

**GAMP-5 Requirement:** UI supports accuracy and ease of use, prevents user errors

**Procedure:**

1. **Homepage (index.tsx)**
   - Navigate to: http://localhost:3000
   - Press **Tab** → Verify focus moves to "Sign In" button
   - Press **Enter** → Verify Clerk sign-in modal opens
   - Press **Escape** → Verify modal closes
   - Press **Tab** until focused on "Sign in to continue" link
   - Press **Enter** → Verify navigates to /sign-in page

2. **Sign-In Page (sign-in.tsx)**
   - Navigate to: http://localhost:3000/sign-in
   - Press **Tab** through all form fields (email, password)
   - Verify each field receives visible focus indicator
   - Enter credentials and press **Tab** to "Sign In" button
   - Press **Enter** → Verify successful authentication

3. **Dashboard Page (dashboard.tsx)**
   - Press **Tab** → Verify first focused element is "Skip to main content" link
   - Press **Enter** on skip link → Verify focus moves to main content area
   - Press **Tab** → Verify focus moves through logo, "Dashboard" link, "Observability" link
   - Verify active page ("Dashboard") has distinct visual indication
   - Press **Tab** to user profile, then **UserButton**
   - Press **Enter** → Verify user menu opens
   - Press **Escape** → Verify menu closes

4. **Observability Page (observability.tsx)**
   - Navigate to: http://localhost:3000/observability (via keyboard)
   - Press **Tab** → Verify skip link receives focus first
   - Press **Enter** on skip link → Verify focus moves to main content
   - Press **Tab** through summary cards
   - Press **Tab** to metrics table
   - Press **Arrow keys** → Verify table cell navigation (if applicable)
   - Verify no focus traps (can navigate forward and backward freely)

5. **Route Changes**
   - From Dashboard, press **Tab** to "Observability" link
   - Press **Enter** → Verify navigation occurs
   - **Expected:** Focus moves to main content area automatically
   - Verify screen reader announces page change

**Pass Criteria:**
- ✅ All interactive elements reachable via keyboard
- ✅ Visible focus indicator on all elements
- ✅ Logical focus order (top to bottom, left to right)
- ✅ No focus traps (can always navigate away)
- ✅ Focus management on route changes works correctly
- ✅ Skip link functional

**Failure Modes:**
- ❌ Element cannot be reached via keyboard → CRITICAL
- ❌ No visible focus indicator → SERIOUS
- ❌ Focus order illogical → MODERATE

---

### TP-A11Y-002: Screen Reader Test (NVDA)

**Objective:** Verify all content and functionality is perceivable and operable via screen reader

**WCAG Criteria:** 1.1.1 Non-text Content, 1.3.1 Info and Relationships, 4.1.2 Name, Role, Value

**GAMP-5 Requirement:** UI facilitates proper entry, review, and approval of records

**Procedure:**

1. **Enable NVDA**
   - Press **Ctrl + Alt + N** to start NVDA
   - Navigate to: http://localhost:3000

2. **Test Landmarks Navigation**
   - Press **D** (next landmark) repeatedly
   - **Expected announcements:**
     - "banner landmark"
     - "navigation landmark"
     - "main landmark"
     - "contentinfo landmark"
   - Verify all regions announced correctly

3. **Test Headings Navigation**
   - Navigate to Dashboard page
   - Press **H** (next heading) repeatedly
   - **Expected announcements:**
     - "Welcome, [User Name]! heading level 1"
     - "User Profile heading level 2"
     - "GAMP-5 Test Suite Generation heading level 2"
     - "Compliance Information heading level 3"
   - Verify heading hierarchy is logical (h1 → h2 → h3)

4. **Test Form Labels (Sign-In Page)**
   - Navigate to /sign-in
   - Press **Tab** to email field
   - **Expected:** "Email edit" or "Email address edit" announced
   - Press **Tab** to password field
   - **Expected:** "Password edit" announced
   - Enter invalid email → Trigger validation error
   - **Expected:** Error message announced via aria-live region

5. **Test ARIA Live Regions**
   - Navigate to Observability page
   - While page is loading:
     - **Expected:** "Loading metrics from LangFuse Cloud. Please wait..." announced
   - If data loads successfully:
     - **Expected:** Dynamic content announced (or focus moves to content)
   - If error occurs:
     - **Expected:** "Failed to load metrics" announced immediately (aria-live="assertive")

6. **Test Table Navigation**
   - Navigate to Observability page (with data)
   - Press **T** (next table)
   - **Expected:** "Table with 4 columns and X rows" announced
   - Press **Ctrl + Alt + Arrow Keys** to navigate table cells
   - **Expected:** Column headers announced with each cell
     - "Date column header: Mon, Nov 11, 2025"
     - "Traces column header: 42"
     - "Cost column header: $1.23"
     - "Models Used column header: deepseek-chat"

7. **Test Links and Buttons**
   - Navigate to Dashboard
   - Press **K** (next link) repeatedly
   - Verify each link announced with:
     - Link text
     - Current page status (if applicable): "Dashboard link, current page"
   - Press **B** (next button)
   - Verify UserButton announced as "button" or "User options button"

8. **Test Loading States**
   - Sign out and sign back in (to trigger loading state)
   - During loading on Dashboard:
     - **Expected:** "Loading dashboard content. Verifying your EU-compliant session..." announced
   - Verify loading state is perceivable without visual cues

**Pass Criteria:**
- ✅ All landmarks announced correctly
- ✅ Heading hierarchy logical and complete
- ✅ Form fields have accessible labels
- ✅ Validation errors announced
- ✅ ARIA live regions announce dynamic content
- ✅ Table structure announced with headers
- ✅ Links and buttons have descriptive names
- ✅ Loading states announced

**Failure Modes:**
- ❌ Missing landmark → SERIOUS
- ❌ Unlabeled form field → CRITICAL
- ❌ Silent error state → CRITICAL
- ❌ Table structure not announced → SERIOUS

---

### TP-A11Y-003: Focus Visibility Test

**Objective:** Verify keyboard focus is always visible

**WCAG Criteria:** 2.4.7 Focus Visible (Level AA)

**GAMP-5 Requirement:** Pharmaceutical environments may have poor lighting; focus must be highly visible

**Procedure:**

1. **Normal Lighting Conditions**
   - Navigate through all pages using **Tab**
   - Verify every focused element has a visible indicator:
     - Blue ring (focus-visible:ring-2 ring-blue-600)
     - Distinct from hover state
     - Visible on white, gray, and colored backgrounds
   - Test on:
     - Skip link (should only show on focus, not at rest)
     - Logo link
     - Navigation links (Dashboard, Observability)
     - UserButton
     - Sign-in form fields
     - Buttons
     - Table cells (if focusable)

2. **High Contrast Mode (Windows)**
   - Enable High Contrast Mode: Settings → Accessibility → Contrast themes → "High Contrast Black"
   - Repeat keyboard navigation test
   - Verify focus indicators remain visible
   - Verify pharmaceutical blue color scheme adapts correctly

3. **Dark Mode (if implemented)**
   - Enable dark mode (future enhancement)
   - Verify focus indicators remain visible
   - Verify contrast ratios still meet WCAG 2.1 AA

4. **Focus Recovery After Interactions**
   - Open UserButton menu → Close menu
   - **Expected:** Focus returns to UserButton
   - Open Clerk sign-in modal → Close modal
   - **Expected:** Focus returns to trigger button
   - Navigate to Observability → Return to Dashboard
   - **Expected:** Focus moves to main content (via focus management)

**Pass Criteria:**
- ✅ Focus indicator visible on all interactive elements
- ✅ Focus indicator contrast ratio ≥ 3:1 against background
- ✅ Focus indicator distinct from hover/active states
- ✅ Focus indicator visible in high contrast mode
- ✅ Focus restored correctly after interactions

**Failure Modes:**
- ❌ No focus indicator → CRITICAL
- ❌ Focus indicator invisible on certain backgrounds → SERIOUS
- ❌ Focus lost after interaction → SERIOUS

---

### TP-A11Y-004: Color Contrast Test

**Objective:** Verify all text and UI components meet WCAG 2.1 AA contrast requirements

**WCAG Criteria:** 1.4.3 Contrast (Minimum) Level AA, 1.4.11 Non-text Contrast Level AA

**GAMP-5 Requirement:** Maintain legibility, accuracy, and traceability

**Procedure:**

1. **Automated Testing (axe DevTools)**
   - Install axe DevTools browser extension
   - Navigate to each page:
     - http://localhost:3000 (Homepage)
     - http://localhost:3000/sign-in
     - http://localhost:3000/dashboard
     - http://localhost:3000/observability
   - Run axe DevTools scan
   - Review "Color Contrast" category
   - Document any violations with screenshots

2. **Manual Verification (Colour Contrast Analyser)**
   - Install Colour Contrast Analyser (CCA) tool
   - Test key text colors:
     - **Primary text (text-gray-900):** #111827 on #FFFFFF
       - Expected: ≥ 4.5:1 contrast ratio
     - **Secondary text (text-gray-600):** #4B5563 on #F9FAFB
       - Expected: ≥ 4.5:1 contrast ratio
     - **Pharmaceutical blue (text-blue-600):** #2563EB on #FFFFFF
       - Expected: ≥ 4.5:1 contrast ratio
     - **Error text (text-red-700):** #B91C1C on #FEF2F2
       - Expected: ≥ 4.5:1 contrast ratio
     - **Success text (text-green-600):** #16A34A on #FFFFFF
       - Expected: ≥ 4.5:1 contrast ratio

3. **UI Component Contrast (Non-text)**
   - Test focus indicators:
     - Blue ring (#2563EB) on white/gray backgrounds
     - Expected: ≥ 3:1 contrast ratio
   - Test borders:
     - Input borders, card borders, table borders
     - Expected: ≥ 3:1 contrast ratio
   - Test status indicators:
     - Loading skeletons, badges, alerts
     - Expected: ≥ 3:1 contrast ratio

4. **Pharmaceutical-Specific Elements**
   - Compliance badges (GAMP-5, ALCOA+, 21 CFR Part 11)
   - ALCOA+ annotations (observability.tsx)
   - Validation status indicators (future: pass/fail badges)
   - Ensure all use sufficient contrast

**Pass Criteria:**
- ✅ All text ≥ 4.5:1 contrast (normal), ≥ 3:1 (large text 18pt+)
- ✅ All UI components ≥ 3:1 contrast
- ✅ No axe DevTools contrast violations
- ✅ Manual verification confirms ratios
- ✅ Pharmaceutical blue palette compliant

**Failure Modes:**
- ❌ Text contrast < 4.5:1 → CRITICAL
- ❌ UI component contrast < 3:1 → SERIOUS
- ❌ Error/warning text insufficient contrast → CRITICAL

---

### TP-A11Y-005: ARIA Live Region Test

**Objective:** Verify dynamic content changes are announced to screen readers

**WCAG Criteria:** 4.1.3 Status Messages (Level AA)

**GAMP-5 Requirement:** Critical pharmaceutical alerts (drug interactions, validation failures) must be accessible

**Procedure:**

1. **Loading States**
   - Enable NVDA
   - Navigate to Dashboard page (sign out first to trigger loading)
   - During loading:
     - **Expected (NVDA):** "Loading dashboard content. Verifying your EU-compliant session..."
   - Navigate to Observability page (with no cached data)
   - During loading:
     - **Expected (NVDA):** "Loading metrics from LangFuse Cloud. Please wait..."

2. **Error States**
   - Disconnect network or configure invalid LangFuse credentials
   - Navigate to Observability page
   - When error occurs:
     - **Expected (NVDA):** "Failed to load metrics" announced immediately (aria-live="assertive")
   - Verify error details are also readable:
     - Press **Down Arrow** to read error message and troubleshooting steps

3. **Success States (Future: SWR Updates)**
   - Navigate to Observability page with valid data
   - Trigger data refresh (manual or auto)
   - When data updates:
     - **Expected (NVDA):** Content update announced (aria-live="polite")
   - Verify dashboard metrics (Total Traces, Cost) announced

4. **Form Validation Errors (Clerk)**
   - Navigate to Sign-In page
   - Enter invalid email (e.g., "notanemail")
   - Press Tab or Enter to trigger validation
   - **Expected (NVDA):** Validation error announced immediately
   - Verify error message associated with field (aria-describedby)

**Pass Criteria:**
- ✅ Loading states announced via aria-live="polite"
- ✅ Error states announced via aria-live="assertive"
- ✅ Dynamic content updates announced
- ✅ Form validation errors announced
- ✅ Announcements occur without moving focus

**Failure Modes:**
- ❌ Silent loading state → SERIOUS
- ❌ Silent error state → CRITICAL
- ❌ Silent form validation → CRITICAL

---

### TP-A11Y-006: Skip Link Test

**Objective:** Verify skip link allows bypassing repeated navigation

**WCAG Criteria:** 2.4.1 Bypass Blocks (Level A)

**GAMP-5 Requirement:** Efficiency in validation testing workflows

**Procedure:**

1. **Visual Test**
   - Navigate to Dashboard page
   - Press **Tab** once
   - **Expected:** "Skip to main content" link becomes visible at top-left
   - Verify styling:
     - Background: Blue (#2563EB)
     - Text: White
     - Position: Absolute, top-0, left-0, z-50
     - Padding: 1rem
     - Focus ring: Blue ring (#1E40AF)

2. **Functional Test**
   - Press **Tab** once (skip link focused)
   - Press **Enter**
   - **Expected:** Focus moves to main content area (id="main-content")
   - Verify main content receives focus (tabIndex={-1})
   - Verify no visible focus ring on main (focus:outline-none)

3. **Keyboard-Only Navigation Efficiency**
   - Without skip link (count):
     - Tab presses from page top to main content: ~5 (logo, 2 nav links, user name, UserButton)
   - With skip link (count):
     - Tab presses from page top to main content: 1 (skip link → Enter)
   - **Expected:** Skip link reduces navigation by ~80%

4. **Screen Reader Test**
   - Enable NVDA
   - Navigate to Dashboard
   - Press **Tab**
   - **Expected (NVDA):** "Skip to main content link"
   - Press **Enter**
   - **Expected (NVDA):** "Main landmark" announced (focus moved to main region)

**Pass Criteria:**
- ✅ Skip link appears on first Tab press
- ✅ Skip link visually distinct and readable
- ✅ Skip link functional (moves focus to main content)
- ✅ Main content receives focus programmatically
- ✅ Screen reader announces skip link and destination

**Failure Modes:**
- ❌ Skip link not visible on focus → CRITICAL
- ❌ Skip link does not move focus → CRITICAL
- ❌ Main content not focusable → SERIOUS

---

### TP-A11Y-007: Table Accessibility Test

**Objective:** Verify data tables are accessible to screen readers

**WCAG Criteria:** 1.3.1 Info and Relationships (Level A)

**GAMP-5 Requirement:** Pharmaceutical data tables (medication inventory, lab results) must be navigable

**Procedure:**

1. **Table Structure Test (Visual)**
   - Navigate to Observability page (ensure data present)
   - Inspect "Daily Metrics (Last 7 Days)" table
   - Verify HTML structure:
     - `<table>` element
     - `<caption>` element (visually hidden, sr-only)
     - `<thead>` with `<tr>` and `<th scope="col">`
     - `<tbody>` with `<tr>` and `<td>`
   - Right-click table → Inspect → Verify scope attributes

2. **Screen Reader Test (NVDA)**
   - Enable NVDA
   - Navigate to Observability page
   - Press **T** (next table)
   - **Expected (NVDA):** "Table with 4 columns and X rows"
   - **Expected (NVDA):** Caption announced: "Daily observability metrics for the last 7 days, showing trace counts, costs, and models used per date"

3. **Table Navigation Test**
   - With NVDA enabled, focus on table
   - Press **Ctrl + Alt + Right Arrow** (next cell)
   - **Expected (NVDA):** "Date column header: Mon, Nov 11, 2025"
   - Press **Ctrl + Alt + Right Arrow** again
   - **Expected (NVDA):** "Traces column header: 42"
   - Continue through all cells
   - Verify column headers announced with each cell

4. **Row Header Test (if applicable)**
   - If table has row headers (scope="row"), test with:
     - Press **Ctrl + Alt + Down Arrow** (next row)
     - **Expected (NVDA):** Row header announced with cell content

**Pass Criteria:**
- ✅ Table has caption (visible or sr-only)
- ✅ All header cells use `<th>` with scope="col"
- ✅ Screen reader announces table dimensions
- ✅ Column headers announced with each cell
- ✅ Table navigable via keyboard (arrow keys with NVDA)

**Failure Modes:**
- ❌ No caption → MODERATE
- ❌ Missing `<th>` or scope attributes → CRITICAL
- ❌ Column headers not announced → CRITICAL

---

### TP-A11Y-008: Form Accessibility Test

**Objective:** Verify forms meet accessibility requirements

**WCAG Criteria:** 3.3.1 Error Identification, 3.3.2 Labels or Instructions, 4.1.2 Name, Role, Value

**GAMP-5 Requirement:** Form validation critical for pharmaceutical data entry

**Procedure:**

1. **Form Label Test (Sign-In Page)**
   - Navigate to /sign-in
   - Inspect form fields with browser DevTools
   - Verify each input has:
     - Associated `<label>` element
     - OR aria-label attribute
     - OR aria-labelledby attribute
   - Verify labels are visible (not hidden or off-screen)

2. **Error Identification Test**
   - Enter invalid email (e.g., "test")
   - Press Tab or Enter to trigger validation
   - Verify error message:
     - Displayed visually (red text)
     - Associated with field (aria-describedby="error-id")
     - Field marked invalid (aria-invalid="true")
   - Enable NVDA
   - Repeat test
   - **Expected (NVDA):** Error announced immediately

3. **Required Field Indication Test**
   - Inspect form fields
   - Verify required fields indicated:
     - Visual asterisk (*) OR "Required" label
     - aria-required="true" attribute
   - Attempt to submit form without required fields
   - Verify error messages for each missing field

4. **Keyboard Interaction Test**
   - Press **Tab** through form fields
   - Verify logical order (top to bottom)
   - Press **Enter** in final field
   - Verify form submission (or validation trigger)
   - Verify no focus traps

**Pass Criteria:**
- ✅ All form fields have accessible labels
- ✅ Validation errors identified and announced
- ✅ Required fields indicated visually and programmatically
- ✅ Keyboard navigation logical
- ✅ Form submittable via keyboard

**Failure Modes:**
- ❌ Unlabeled form field → CRITICAL
- ❌ Silent validation error → CRITICAL
- ❌ Required field not indicated → SERIOUS

---

## Test Execution

### Test Cycle
- **Frequency:** Every major release, after accessibility fixes, on-demand for audits
- **Duration:** ~2-4 hours (all procedures)
- **Testers:** QA engineers with accessibility training
- **Tools:** NVDA, axe DevTools, Colour Contrast Analyser

### Test Reporting
- Document results in: `test-results-YYYYMMDD.md`
- Include:
  - Test ID, procedure name, date, tester
  - Pass/fail status for each criterion
  - Screenshots of violations
  - Screen reader transcripts (text or audio)
  - Severity ratings (Critical, Serious, Moderate, Minor)
  - Remediation recommendations

### Defect Management
- Critical defects: Block release
- Serious defects: Fix before release (may require exception approval)
- Moderate defects: Schedule for next sprint
- Minor defects: Backlog

---

## Compliance Mapping

### WCAG 2.1 AA Success Criteria Tested
- 1.1.1 Non-text Content (TP-A11Y-002)
- 1.3.1 Info and Relationships (TP-A11Y-002, TP-A11Y-007)
- 1.4.3 Contrast (Minimum) (TP-A11Y-004)
- 1.4.11 Non-text Contrast (TP-A11Y-004)
- 2.1.1 Keyboard (TP-A11Y-001)
- 2.4.1 Bypass Blocks (TP-A11Y-006)
- 2.4.3 Focus Order (TP-A11Y-001)
- 2.4.7 Focus Visible (TP-A11Y-003)
- 3.3.1 Error Identification (TP-A11Y-008)
- 3.3.2 Labels or Instructions (TP-A11Y-008)
- 4.1.2 Name, Role, Value (TP-A11Y-002, TP-A11Y-008)
- 4.1.3 Status Messages (TP-A11Y-005)

### GAMP-5 UI Validation Requirements
- User Requirements Traceability: All tests linked to WCAG criteria
- Risk Assessment: Severity ratings (Critical, Serious, Moderate, Minor)
- Verification Testing: Evidence captured (screenshots, transcripts)
- Audit Trail: Test results stored in Git repository
- User Interface Design: Focus on accuracy, legibility, error prevention

### 21 CFR Part 11 (Future)
- Electronic Signature UI: Not yet implemented (defer to Phase 5)
- Audit Trail Visualization: Tested via Observability page (TP-A11Y-007)

---

## References
- WCAG 2.1 Guidelines: https://www.w3.org/TR/WCAG21/
- NVDA User Guide: https://www.nvaccess.org/files/nvda/documentation/userGuide.html
- axe DevTools: https://www.deque.com/axe/devtools/
- Colour Contrast Analyser: https://www.tpgi.com/color-contrast-checker/
- GAMP-5 Guide: https://ispe.org/publications/guidance-documents/gamp-5

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Next Review:** After implementation of fixes + test execution
**Approval Required:** Yes (QA lead, validation team)
**Traceability:** Links to WCAG 2.1 AA, GAMP-5, audit findings document
