# Anti-Patterns: Explicit Avoidance Checklist

## Purpose

This document provides an **explicit rejection list** of convergent design patterns that lead to generic "AI slop" aesthetics.

**Use this checklist to validate** every design implementation before marking complete.

---

## Typography Anti-Patterns

### ❌ NEVER Use These Fonts

**Generic Sans-Serifs**:
- Inter
- Roboto
- Arial
- Helvetica
- system-ui, -apple-system, BlinkMacSystemFont

**Detection**:
```bash
grep -r "font-family.*Inter" frontend/
grep -r "Roboto" frontend/
grep -r "Arial" frontend/
```

**Fix**: Replace with distinctive fonts (Space Grotesk, Clash Display, Cabinet Grotesk, Instrument Sans)

---

### ❌ NEVER Use All One Weight

**Example of Bad Practice**:
```css
h1, h2, h3, p { font-weight: 400; }
```

**Why it fails**: No hierarchy, no visual interest

**Fix**: Strategic weight variation
```css
h1 { font-weight: 700; }  /* Bold for impact */
h2 { font-weight: 600; }  /* Semibold for structure */
p  { font-weight: 400; }  /* Normal for readability */
```

---

## Color Anti-Patterns

### ❌ NEVER Use Purple Gradients (AI Default)

**Specific Colors to Reject**:
- `#6366f1` (Indigo 500)
- `#8b5cf6` (Violet 500)
- `#a78bfa` (Violet 400)
- Any purple gradient on white/light background

**Detection**:
```bash
grep -r "#6366f1\|#8b5cf6\|#a78bfa" frontend/
```

**Why it fails**: Every AI-generated landing page uses this

**Fix**: Choose context-specific color palette (cyan for tech, warm tones for organic, etc.)

---

### ❌ NEVER Use Evenly-Distributed Palettes

**Example of Bad Practice**:
```css
:root {
  --color-1: #3b82f6;  /* 20% usage */
  --color-2: #10b981;  /* 20% usage */
  --color-3: #f59e0b;  /* 20% usage */
  --color-4: #ef4444;  /* 20% usage */
  --color-5: #8b5cf6;  /* 20% usage */
}
```

**Why it fails**: No dominant hue, looks scattered and indecisive

**Fix**: 60-30-10 rule with dominant color
```css
:root {
  --color-background: #0a0e27;   /* 60% */
  --color-primary: #06b6d4;      /* 30% */
  --color-accent: #ffffff;       /* 10% */
}
```

---

## Layout Anti-Patterns

### ❌ NEVER Use Centered Symmetric Hero

**Example of Bad Practice**:
```tsx
<section className="grid grid-cols-2 gap-8 items-center">
  <div>Text Content</div>
  <div>Image</div>
</section>
```

**Why it fails**: Predictable, templated, seen on 90% of landing pages

**Fix**: Asymmetric layout with intentional visual hierarchy
```tsx
<section className="grid lg:grid-cols-[60%_40%] gap-0">
  <div className="px-12 py-24">Dominant Text (60%)</div>
  <div className="relative overflow-visible">3D Element (40%)</div>
</section>
```

---

### ❌ NEVER Use Predictable Section Stacking

**Example of Bad Practice**:
```tsx
<main>
  <section>Hero</section>
  <section>Features (3 columns)</section>
  <section>Testimonials (3 columns)</section>
  <section>CTA</section>
</main>
```

**Why it fails**: Cookie-cutter template structure

**Fix**: Add spatial variation
- Overlapping sections (negative margins)
- Diagonal elements (transform: rotate)
- Asymmetric grids
- Elements escaping containers (overflow-visible)

---

## Animation Anti-Patterns

### ❌ NEVER Use Simple Fade-Ins

**Example of Bad Practice**:
```tsx
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
/>
```

**Why it fails**: Generic, no choreography, scattered throughout page

**Fix**: Orchestrated entrance with multiple properties
```tsx
<motion.div
  initial={{ opacity: 0, y: 40, scale: 0.95 }}
  animate={{ opacity: 1, y: 0, scale: 1 }}
  transition={{
    duration: 0.6,
    delay: 0.2,  // Part of staggered sequence
    ease: [0.43, 0.13, 0.23, 0.96]
  }}
/>
```

---

### ❌ NEVER Use Scattered Micro-Interactions

**Example of Bad Practice**:
- Random hover effects throughout page
- Unrelated animations triggering at different times
- No high-impact "moment"

**Why it fails**: Lacks cohesive choreography

**Fix**: Consolidate into high-impact moments
- **Page load**: One orchestrated entrance sequence
- **Scroll**: One parallax effect with depth
- **Hover**: Dramatic state changes on key CTAs only

---

## Component Anti-Patterns

### ❌ NEVER Use Generic Card Grids

**Example of Bad Practice**:
```tsx
<div className="grid grid-cols-3 gap-4">
  <div className="bg-white rounded-lg p-6 shadow">Card 1</div>
  <div className="bg-white rounded-lg p-6 shadow">Card 2</div>
  <div className="bg-white rounded-lg p-6 shadow">Card 3</div>
</div>
```

**Why it fails**: Every SaaS site has this

**Fix**: Break the grid
```tsx
<div className="grid grid-cols-3 gap-8">
  <div className="col-span-2 row-span-2 transform -rotate-1">Featured Card</div>
  <div className="transform rotate-2">Card 2</div>
  <div className="col-start-3 row-start-2">Card 3</div>
</div>
```

---

### ❌ NEVER Use Standard Button Styles

**Example of Bad Practice**:
```tsx
<button className="bg-blue-500 text-white px-4 py-2 rounded">
  Click Me
</button>
```

**Why it fails**: Generic Tailwind default

**Fix**: Bold, context-specific styling
```tsx
<motion.button
  className="bg-primary px-8 py-4 rounded-full font-semibold text-lg shadow-lg shadow-primary/25"
  whileHover={{ scale: 1.05, boxShadow: "0 0 40px rgba(6, 182, 212, 0.6)" }}
  whileTap={{ scale: 0.95 }}
>
  Get Started
</motion.button>
```

---

## Validation Checklist

Run this checklist before marking design complete:

### Typography
- [ ] **No Inter/Roboto/Arial** in codebase
- [ ] Display and body fonts are distinctive
- [ ] Weight variations used strategically (not all 400)
- [ ] Line height adjusted (tight for headlines, loose for body)
- [ ] Letter spacing intentional

### Color
- [ ] **No purple gradients** (#6366f1, #8b5cf6)
- [ ] Dominant color has 60%+ visual weight
- [ ] Accent colors used sparingly (10%)
- [ ] Gradients intentional (not default)
- [ ] Contrast ratios meet WCAG AA

### Layout
- [ ] **No centered symmetric hero**
- [ ] Asymmetric or grid-breaking elements present
- [ ] Sections have spatial variation (overlap, rotation)
- [ ] Elements escape containers where appropriate

### Animation
- [ ] **No simple fade-ins** without choreography
- [ ] Orchestrated entrance sequence implemented
- [ ] High-impact moments identified (load, scroll, hover)
- [ ] Animations consolidated (not scattered)

### Overall
- [ ] Design has clear aesthetic direction (not generic)
- [ ] One memorable differentiator identified
- [ ] Context-specific choices (not templated)
- [ ] `validate_design.py` passes with zero warnings

---

## Common Convergent Patterns by Use Case

### SaaS Landing Page Convergence

**Typical AI Output** (reject all):
- Inter font
- Purple gradient hero (#6366f1 → #8b5cf6)
- Centered two-column layout
- Three-column feature cards
- Simple fade-in animations
- Generic "Get Started" CTA

**Bold Alternative**:
- Space Grotesk + Instrument Sans
- Dark background + cyan accents (#06b6d4)
- Asymmetric 60/40 hero with 3D element
- Broken grid with overlapping cards
- Orchestrated entrance + parallax scroll
- Context-specific CTA ("Start Validating")

---

### Portfolio/Agency Convergence

**Typical AI Output** (reject all):
- System fonts
- Black/white minimalism (but boring)
- Standard grid gallery
- Hover opacity changes only
- No spatial variation

**Bold Alternative**:
- Cabinet Grotesk + Editorial serif
- Duotone palette (red + blue)
- Diagonal grid with perspective
- Dramatic hover effects (scale, rotate, glow)
- Overlapping sections, z-index layering

---

### E-commerce Convergence

**Typical AI Output** (reject all):
- Roboto font
- Generic product grid (4 columns)
- White background, minimal color
- Standard card shadows
- Basic add-to-cart buttons

**Bold Alternative**:
- Plus Jakarta Sans + Lora (serif)
- Rich color palette (brand-specific)
- Asymmetric product layout with featured items
- Layered cards with depth
- Animated CTAs with state changes

---

## Detection Scripts

### Find Generic Fonts
```bash
grep -r "font-family.*Inter" frontend/
grep -r "Roboto" frontend/
grep -r "Arial" frontend/
grep -r "system-ui" frontend/
```

### Find Generic Colors
```bash
grep -r "#6366f1" frontend/
grep -r "#8b5cf6" frontend/
grep -r "#a78bfa" frontend/
```

### Find Generic Layouts
```bash
grep -r "grid-cols-2.*gap-8" frontend/
grep -r "grid-cols-3.*gap-4" frontend/
```

### Find Simple Animations
```bash
grep -r "initial.*opacity.*0.*animate.*opacity.*1" frontend/
```

---

## The Ultimate Test

**Ask yourself**:

> "If I removed all branding and showed this to 100 people, would they say it looks like every other website, or would they remember it?"

**If the answer is "every other website":**
- ❌ You have converged on generic patterns
- ❌ Design fails the anti-pattern checklist
- ✅ **Start over with bolder choices**

**If the answer is "they would remember it":**
- ✅ You have achieved bold, distinctive design
- ✅ Anti-pattern checklist passes
- ✅ **Ready for user confirmation**

---

**Remember**: This checklist is **mandatory**, not optional. Every item must pass before claiming design completion.
