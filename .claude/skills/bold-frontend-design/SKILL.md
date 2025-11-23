---
name: bold-frontend-design
description: Creates visually striking, production-grade frontend interfaces that reject generic "AI slop" aesthetics through intentional design thinking. Implements bold typography, distinctive color palettes, high-impact animations (React Three Fiber, Framer Motion), and unexpected spatial compositions. Use PROACTIVELY when building landing pages, hero sections, 3D visualizations, or any interface requiring memorable visual impact. MUST BE USED when user requests "creative", "bold", "unique", "striking", "3D", "animated", or "next-level" design.
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob"]
model: claude-sonnet-4-5-20250929
---

# Bold Frontend Design Skill

## Philosophy: Rejecting AI Convergence

### The Problem: Generic "AI Slop" Aesthetics

Claude naturally samples from **high-probability design patterns** found in training data:
- Inter/Roboto fonts everywhere
- Purple gradients on white backgrounds (#6366f1, #8b5cf6)
- Centered hero sections with symmetric columns
- Simple fade-in animations
- Cookie-cutter layouts lacking context-specific character

**This creates convergent "slop"** - designs that are safe, predictable, and forgettable.

### The Solution: Intentional Creative Direction

**Steerability as a feature**: Claude responds dramatically to specific guidance pushing away from convention.

**Core Principle**: "Make unexpected choices that feel genuinely designed for the context."

Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
Bold maximalism and refined minimalism both work - **the key is intentionality, not intensity**.

### The Anti-Convergence Mandate

**CRITICAL**: You must continuously resist ANY safety convergence, even after implementing creative directives. **Think outside the box** at every decision point.

---

## Prerequisites

Before invoking this skill, verify:

1. **Project Type**: Next.js or React application
2. **Mindset**: User is willing to push creative boundaries
3. **Access**: Ability to install npm packages
4. **Environment**: Development server can be tested (localhost)

**Dependencies** (will be installed as needed):
- `@react-three/fiber` - React renderer for Three.js
- `@react-three/drei` - Helper components
- `@react-three/postprocessing` - Post-processing effects (Bloom, etc.)
- `framer-motion` - Animation library
- `three` - Core 3D library

---

## CRITICAL: Anti-Convergence Protocol

### NEVER Use (Explicit Rejection List)

**Fonts**:
- ❌ Inter
- ❌ Roboto
- ❌ Arial
- ❌ Helvetica
- ❌ System fonts (system-ui, -apple-system, BlinkMacSystemFont)

**Colors**:
- ❌ Purple gradients (#6366f1, #8b5cf6, #a78bfa on white/light backgrounds)
- ❌ Generic Tailwind defaults without customization
- ❌ Evenly-distributed palettes lacking dominant hues

**Layouts**:
- ❌ Centered hero with symmetric two-column grid
- ❌ Predictable section stacking without spatial variation
- ❌ Standard grid patterns (3-column cards, etc.) without breaks

**Animations**:
- ❌ Simple fade-ins without choreography
- ❌ Scattered micro-interactions lacking purpose
- ❌ Predictable hover effects (opacity change only)

### ALWAYS Verify (Before Proceeding)

Before implementing ANY design element, ask:

1. **Have I seen this pattern in 100 other websites?** → If yes, choose differently
2. **Is this choice safe or bold?** → If safe, push further
3. **Does this reflect the specific context, or is it generic?** → Must be context-specific
4. **Am I converging on a local maximum of safety?** → Continuous pushback required

**If answers are Yes/Safe/Generic/Converging → STOP and choose differently**

---

## Workflow Phases

### Phase 1: Design Thinking (10-15 minutes) - PRE-CODE

**Objective**: Establish intentional creative direction before writing a single line of code.

**Steps**:

1. **Define Purpose and Audience**
   - What problem does this interface solve?
   - Who is the target user?
   - What emotion/action should it inspire?

   Example: "Landing page for pharmaceutical AI validation tool. Audience: technical decision-makers (CTOs, validation engineers). Emotion: Trust + innovation."

2. **Select Extreme Aesthetic Tone**

   Choose ONE direction and commit fully:

   - **Brutalist**: Raw, unstyled elements, bold typography, stark contrasts
   - **Maximalist**: Layered complexity, rich textures, abundant visual elements
   - **Retro-Futuristic**: 80s neon, synthwave, chrome effects, grid perspectives
   - **Organic**: Flowing curves, natural movements, soft gradients, biomimicry
   - **Luxury**: Elegant restraint, premium materials (gold, marble textures), sophisticated
   - **Playful**: Vibrant colors, unexpected interactions, whimsical illustrations
   - **Editorial**: Magazine-inspired, bold typography hierarchy, sophisticated grids

   **Document choice**: "Aesthetic: Retro-futuristic with organic elements - Tron-like glass molecules on dark gradients"

3. **Identify One Memorable Differentiator**

   What single element will make this design unforgettable?

   Examples:
   - Interactive 3D molecular visualization with bloom effects
   - Diagonal scroll-triggered reveals
   - Variable font weight animation on scroll
   - Asymmetric overlapping sections with parallax

   **Document choice**: "Differentiator: Glass molecule 3D visualization with Bloom glow in hero section"

4. **Document Constraints**

   Technical requirements that inform implementation:
   - Framework: Next.js 14 (Pages Router)
   - Performance: 60fps animations, LCP <2.5s
   - Accessibility: WCAG AA minimum
   - Browser: Modern browsers (ES6+)

**Quality Gate**: Design philosophy document created (can be in comments or separate file)

**Output Example**:
```markdown
# Design Philosophy: PharmaGen AI

**Purpose**: Landing page to convert CTOs/validation engineers to try AI test generation
**Audience**: Technical decision-makers who value innovation but require trust
**Aesthetic**: Retro-futuristic + Organic (glass molecules, dark gradients, blue/cyan palette)
**Differentiator**: Interactive 3D molecular visualization with Bloom post-processing
**Tone**: Professional yet cutting-edge, trustworthy yet innovative

**Constraints**:
- Next.js 14 (Pages Router)
- 60fps animations
- WCAG AA compliance
- Modern browsers only
```

---

### Phase 2: Rejection of Generic Patterns (5-10 minutes)

**Objective**: Explicitly document what NOT to do, creating guardrails against convergence.

**Steps**:

1. **List Generic Patterns to Avoid**

   Based on aesthetic choice, identify specific convergent patterns:

   ```markdown
   ## Anti-Pattern Checklist

   **Typography**:
   - ❌ Inter, Roboto (use Space Grotesk, Clash Display, Cabinet Grotesk instead)

   **Colors**:
   - ❌ Purple gradients (#6366f1)
   - ✅ Cyan/blue gradients (#06b6d4, #0ea5e9, #3b82f6) with sharp white accents

   **Layout**:
   - ❌ Centered hero with symmetric columns
   - ✅ Asymmetric hero with 3D element on left, text on right

   **Animations**:
   - ❌ Simple fade-ins
   - ✅ Orchestrated entrance with staggered 3D + text reveals
   ```

2. **Choose Distinctive Typography**

   Select fonts that have **character**:

   - **Display Fonts** (headings): Space Grotesk, Clash Display, Cabinet Grotesk, Syne, Plus Jakarta Sans
   - **Body Fonts** (paragraphs): Instrument Sans, Manrope, DM Sans, Outfit
   - **Variable Fonts** (dynamic weight): Inter Variable (if customized heavily), Recursive

   **Pair intentionally**: Display font for headlines, complementary sans-serif for body

   **Document choice**:
   ```markdown
   **Typography System**:
   - Headings: Space Grotesk (700, 900 weights)
   - Body: Instrument Sans (400, 500 weights)
   - Code/Monospace: JetBrains Mono
   ```

3. **Define Dominant Color Palette**

   **60-30-10 Rule with Twist**:
   - **60% Dominant**: Deep blue-black (#0a0e27)
   - **30% Secondary**: Cyan gradients (#06b6d4 → #3b82f6)
   - **10% Accent**: Sharp white (#ffffff) + red alerts (#ef4444)

   **Use CSS Variables**:
   ```css
   :root {
     --color-background: #0a0e27;
     --color-primary: #06b6d4;
     --color-primary-light: #3b82f6;
     --color-accent: #ffffff;
     --color-alert: #ef4444;
   }
   ```

4. **Plan Unexpected Spatial Composition**

   How will you break the grid?

   - **Asymmetry**: 60/40 split instead of 50/50
   - **Overlap**: Sections bleed into each other with z-index layering
   - **Diagonal Flow**: Elements on rotated grids (-3deg, 5deg)
   - **Viewport Units**: Full-height sections (100vh) with scroll-snap

   **Document choice**:
   ```markdown
   **Spatial Strategy**:
   - Hero: Asymmetric 60/40 (text left, 3D right)
   - Sections: Overlapping with transparent backgrounds
   - Molecules: Floating outside container bounds (overflow-visible)
   - Scroll: Parallax with different speeds (text: 50%, background: 20%)
   ```

**Quality Gate**: Anti-pattern checklist complete, distinctive choices documented

---

### Phase 3: Implementation with Intentionality (30-60 minutes)

**Objective**: Execute bold design with production-grade code.

**Steps**:

1. **Install Animation Dependencies**

   ```bash
   cd frontend  # or your Next.js directory
   npm install @react-three/fiber @react-three/drei @react-three/postprocessing framer-motion three
   ```

   **Verify installation**:
   ```bash
   npm list @react-three/fiber @react-three/drei framer-motion
   ```

2. **Set Up Typography System**

   **Option A: Google Fonts** (quick)
   ```tsx
   // pages/_app.tsx or layout.tsx
   import { Space_Grotesk, Instrument_Sans } from 'next/font/google';

   const spaceGrotesk = Space_Grotesk({
     subsets: ['latin'],
     weight: ['400', '700'],
     variable: '--font-display',
   });

   const instrumentSans = Instrument_Sans({
     subsets: ['latin'],
     weight: ['400', '500'],
     variable: '--font-body',
   });

   export default function App({ Component, pageProps }) {
     return (
       <div className={`${spaceGrotesk.variable} ${instrumentSans.variable}`}>
         <Component {...pageProps} />
       </div>
     );
   }
   ```

   **Option B: Adobe Fonts / Custom** (distinctive)
   - Link in `_document.tsx` or use `@font-face`

3. **Build Color System**

   **Tailwind Configuration** (if using Tailwind):
   ```js
   // tailwind.config.js
   module.exports = {
     theme: {
       extend: {
         colors: {
           background: '#0a0e27',
           primary: {
             DEFAULT: '#06b6d4',
             light: '#3b82f6',
             dark: '#0891b2',
           },
           accent: '#ffffff',
           alert: '#ef4444',
         },
         fontFamily: {
           display: ['var(--font-display)', 'sans-serif'],
           body: ['var(--font-body)', 'sans-serif'],
         },
       },
     },
   };
   ```

   **CSS Variables** (if not using Tailwind):
   ```css
   /* globals.css */
   :root {
     --color-background: #0a0e27;
     --color-primary: #06b6d4;
     --color-primary-light: #3b82f6;
     --color-accent: #ffffff;
     --color-alert: #ef4444;

     --font-display: 'Space Grotesk', sans-serif;
     --font-body: 'Instrument Sans', sans-serif;
   }
   ```

4. **Create Spatial Composition**

   **Example: Asymmetric Hero Section**
   ```tsx
   <section className="min-h-screen grid lg:grid-cols-[60%_40%] items-center">
     {/* Text Content - Left 60% */}
     <div className="px-12 py-24">
       <h1 className="font-display text-7xl font-bold">
         Validation 4.0 <span className="text-primary">Reimagined.</span>
       </h1>
       <p className="font-body text-xl mt-6">
         Generate GAMP-driven test suites in minutes.
       </p>
     </div>

     {/* 3D Element - Right 40% */}
     <div className="h-full relative">
       <Canvas className="absolute inset-0">
         {/* 3D content */}
       </Canvas>
     </div>
   </section>
   ```

5. **Implement High-Impact Animations**

   **A. Orchestrated Entrance (Framer Motion)**

   Use staggered delays for choreographed reveal:
   ```tsx
   <motion.div
     initial={{ opacity: 0, y: 50 }}
     animate={{ opacity: 1, y: 0 }}
     transition={{ duration: 0.8, delay: 0 }}
   >
     <h1>First Element</h1>
   </motion.div>

   <motion.div
     initial={{ opacity: 0, y: 30 }}
     animate={{ opacity: 1, y: 0 }}
     transition={{ duration: 0.8, delay: 0.2 }}
   >
     <p>Second Element</p>
   </motion.div>

   <motion.div
     initial={{ opacity: 0, scale: 0.8 }}
     animate={{ opacity: 1, scale: 1 }}
     transition={{ duration: 1, delay: 0.4 }}
   >
     <button>Third Element</button>
   </motion.div>
   ```

   **B. Scroll-Triggered Parallax**

   ```tsx
   import { useScroll, useTransform, motion } from 'framer-motion';

   const ref = useRef(null);
   const { scrollYProgress } = useScroll({
     target: ref,
     offset: ["start start", "end start"]
   });

   const yText = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
   const yBackground = useTransform(scrollYProgress, [0, 1], ["0%", "20%"]);

   <section ref={ref}>
     <motion.div style={{ y: yText }}>
       Text moves 50%
     </motion.div>
     <motion.div style={{ y: yBackground }}>
       Background moves 20% (parallax)
     </motion.div>
   </section>
   ```

   **C. React Three Fiber 3D Elements**

   See `templates/hero-3d-parallax.tsx` and `reference/react-three-fiber-cookbook.md` for complete examples.

   **Key Pattern**: Glass molecules with Bloom glow
   ```tsx
   import { Canvas } from '@react-three/fiber';
   import { MeshTransmissionMaterial, Environment, Float } from '@react-three/drei';
   import { EffectComposer, Bloom } from '@react-three/postprocessing';

   <Canvas>
     <ambientLight intensity={0.5} />
     <pointLight position={[10, 10, 10]} intensity={1.5} />
     <Environment preset="city" environmentIntensity={0.8} />

     <Float speed={2} rotationIntensity={0.5}>
       <mesh>
         <sphereGeometry args={[1, 32, 32]} />
         <MeshTransmissionMaterial
           transmission={1}
           thickness={0.3}
           roughness={0}
           ior={1.3}
           chromaticAberration={0.02}
           color="#06b6d4"
           emissive="#06b6d4"
           emissiveIntensity={0.15}
         />
       </mesh>
     </Float>

     <EffectComposer>
       <Bloom
         luminanceThreshold={0}
         luminanceSmoothing={0.9}
         intensity={2.5}
         radius={0.8}
       />
     </EffectComposer>
   </Canvas>
   ```

6. **Grid-Breaking Layouts**

   **Example: Overlapping Sections**
   ```tsx
   <section className="relative z-10 pb-32">
     <div className="bg-white rounded-3xl p-12">
       Content in white box
     </div>
   </section>

   <section className="relative z-20 -mt-16">
     {/* Overlaps previous section by 64px (4rem) */}
     <div className="bg-primary rounded-3xl p-12">
       Overlapping content
     </div>
   </section>
   ```

   **Example: Diagonal Elements**
   ```tsx
   <div className="transform -rotate-3 origin-center">
     <Image src="/hero-image.jpg" alt="Hero" />
   </div>
   ```

**Quality Gate**: All major elements implemented, no generic patterns detected

---

### Phase 4: Refinement and Validation (15-20 minutes)

**Objective**: Ensure quality, performance, and visual impact.

**Steps**:

1. **Run Design Validation Script**

   ```bash
   python .claude/skills/bold-frontend-design/scripts/validate_design.py frontend/
   ```

   **Expected Output**:
   ```
   ✓ No generic fonts detected
   ✓ No generic purple gradients
   ✓ Typography system implemented
   ✓ Animation orchestration present

   Warnings: 0
   Design validation PASSED
   ```

   **If warnings appear**: Fix immediately before proceeding

2. **Check Animation Performance**

   **Chrome DevTools**:
   - Open Performance tab
   - Record 5-second interaction (scroll, hover)
   - Verify: **60fps maintained** (no red bars in FPS meter)

   **If performance issues**:
   - Reduce Bloom intensity
   - Lower sphere geometry segments (32 → 16)
   - Use `will-change: transform` on animated elements
   - Implement scroll throttling

3. **Verify Cohesive Aesthetic Point-of-View**

   **Checklist**:
   - ✅ All elements align with chosen aesthetic tone?
   - ✅ Typography consistent across all sections?
   - ✅ Color palette used cohesively (no random colors)?
   - ✅ Animation style consistent (all orchestrated, or all subtle)?
   - ✅ Spatial composition intentional (not accidental)?

   **If not cohesive**: Identify outliers and bring into alignment

4. **Polish Micro-Interactions**

   **High-Impact Moments**:
   - **Hover on CTA button**: Scale + glow
     ```tsx
     <button className="transition-all hover:scale-105 hover:shadow-2xl hover:shadow-primary/50">
     ```

   - **Scroll indicators**: Animated arrow or gradient bar
     ```tsx
     <motion.div
       animate={{ y: [0, 10, 0] }}
       transition={{ duration: 1.5, repeat: Infinity }}
     >
       ↓
     </motion.div>
     ```

   - **3D hover**: Increase rotation speed
     ```tsx
     const [hovered, setHover] = useState(false);

     useFrame((state, delta) => {
       const speed = hovered ? 3 : 1;
       groupRef.current.rotation.y += delta * 0.2 * speed;
     });

     <mesh onPointerOver={() => setHover(true)} onPointerOut={() => setHover(false)}>
     ```

5. **Test Responsiveness**

   **Breakpoints to Test**:
   - Mobile: 375px, 414px
   - Tablet: 768px, 1024px
   - Desktop: 1280px, 1920px

   **3D Elements on Mobile**:
   - Reduce scale: `<Molecule scale={isMobile ? 0.3 : 0.6} />`
   - Hide complex effects: Only show Bloom on desktop
   - Simplify geometry: Lower segment count on mobile

6. **Accessibility Quick Check**

   - ✅ Color contrast: 4.5:1 for body text, 3:1 for headings (WCAG AA)
   - ✅ Keyboard navigation: Tab through interactive elements
   - ✅ Focus indicators: Visible on all focusable elements
   - ✅ Alt text: All images have descriptive alt attributes
   - ✅ Motion preferences: Respect `prefers-reduced-motion`

   **Reduced motion example**:
   ```tsx
   const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

   <motion.div
     animate={{ opacity: 1, y: 0 }}
     transition={{ duration: prefersReducedMotion ? 0 : 0.8 }}
   >
   ```

7. **User Confirmation - CRITICAL**

   **NEVER claim success without explicit user verification**

   Ask the user:
   ```
   Can you confirm you see the design at http://localhost:3000?

   Does this feel:
   - Bold and distinctive (not generic)?
   - Aligned with the [aesthetic tone] direction?
   - Memorable and impactful?

   Please provide feedback on what stands out and what could be pushed further.
   ```

   **Do NOT proceed to next task until user confirms**

**Quality Gate**: Validation passes, performance targets met, user confirms visual impact

---

## Tool Selection Guide

### When to Use React Three Fiber

**Use R3F When**:
- Creating 3D objects (spheres, boxes, custom geometries)
- Implementing glass/metallic materials
- Building molecular/abstract visualizations
- Adding Bloom post-processing effects
- Floating/rotating 3D elements

**Example Use Cases**:
- Hero section with molecular visualization
- Product showcase with 3D model
- Abstract background elements
- Interactive 3D infographics

**Template**: `templates/hero-3d-parallax.tsx`

### When to Use Framer Motion

**Use Framer Motion When**:
- Orchestrating page entrance animations
- Creating scroll-triggered effects
- Building parallax compositions
- Animating 2D elements (text, cards, buttons)
- Gesture-based interactions (drag, hover)

**Example Use Cases**:
- Staggered text reveals on load
- Scroll-based opacity/position changes
- Parallax hero sections (2D)
- Card hover effects
- Modal/drawer transitions

**Template**: `templates/orchestrated-entrance.tsx`, `templates/scroll-effects.tsx`

### Decision Tree

```
Is the element 3D?
├─ Yes → Use React Three Fiber
│   └─ Need glow/glass effects?
│       ├─ Yes → Add MeshTransmissionMaterial + Bloom
│       └─ No → Use standard materials
│
└─ No → Use Framer Motion
    └─ Triggered by scroll?
        ├─ Yes → Use useScroll + useTransform
        └─ No → Use animate prop
```

### Combining Both

**Pattern**: R3F for 3D Canvas, Framer Motion for 2D overlays

```tsx
<section>
  {/* 3D Background Layer */}
  <div className="absolute inset-0 z-0">
    <Canvas>
      <Float><Molecule /></Float>
      <EffectComposer><Bloom /></EffectComposer>
    </Canvas>
  </div>

  {/* 2D Content Layer */}
  <motion.div
    className="relative z-10"
    initial={{ opacity: 0, y: 50 }}
    animate={{ opacity: 1, y: 0 }}
  >
    <h1>Overlaid Content</h1>
  </motion.div>
</section>
```

---

## Success Criteria

Before marking this skill complete, verify ALL criteria:

### Functional Requirements

- ✅ Design philosophy document created (purpose, aesthetic, differentiator)
- ✅ Anti-pattern checklist complete
- ✅ Typography system implemented (distinctive fonts)
- ✅ Color palette defined (dominant hues with accents)
- ✅ Spatial composition intentional (not default grid)
- ✅ High-impact animations implemented (orchestrated or 3D)

### Design Quality Requirements

- ✅ `validate_design.py` passes with **zero warnings**
- ✅ No generic fonts (Inter, Roboto, Arial) in codebase
- ✅ No generic color schemes (purple gradients)
- ✅ Layout breaks expected grid patterns
- ✅ Animations orchestrated with high-impact moments (not scattered)
- ✅ 3D elements (if used) have distinctive materials (glass, bloom, etc.)
- ✅ Typography feels distinctive and characterful
- ✅ Color palette has dominant hues (not evenly distributed)
- ✅ Cohesive aesthetic point-of-view throughout

### Performance Requirements

- ✅ **60fps** animation performance (Chrome DevTools verification)
- ✅ Lighthouse performance score **>85**
- ✅ First Contentful Paint **<1.5s**
- ✅ No animation jank on scroll

### Accessibility Requirements

- ✅ Color contrast meets WCAG AA (4.5:1 body, 3:1 headings)
- ✅ Keyboard navigation functional
- ✅ Focus indicators visible
- ✅ Alt text on images
- ✅ `prefers-reduced-motion` respected

### User Confirmation (MANDATORY)

- ✅ User has seen the design at localhost URL
- ✅ User explicitly confirms visual impact: "Does this feel bold and distinctive?"
- ✅ **NEVER** claim success without user confirmation

---

## Troubleshooting

### Issue: Design Still Feels Generic

**Symptom**: Implementation complete but lacks distinctive character

**Diagnosis**:
1. Run `validate_design.py` to detect convergent patterns
   ```bash
   python .claude/skills/bold-frontend-design/scripts/validate_design.py frontend/
   ```

2. Check typography choices against generic font list:
   - Search codebase: `grep -r "font-family.*Inter" frontend/`
   - Search codebase: `grep -r "Roboto" frontend/`

3. Verify color palette has dominant hues:
   - Review CSS variables or Tailwind config
   - Check for #6366f1 or #8b5cf6 (generic purple)

4. Review layout for predictable grid patterns:
   - Is hero centered with symmetric columns? → Asymmetric needed
   - Are sections stacked predictably? → Add overlap, rotation

**Solution**:

**A. Replace Generic Fonts Immediately**
```bash
# Find and replace Inter with Space Grotesk
find frontend/ -name "*.tsx" -exec sed -i 's/Inter/Space Grotesk/g' {} +
```

**B. Shift to More Extreme Aesthetic Tone**

If design feels "balanced" or "safe", it's too timid. Push further:
- Maximalist → Add more layers, textures, visual complexity
- Minimalist → Remove more elements, increase whitespace 3x
- Brutalist → Strip away all styling, make typography bolder
- Retro-futuristic → Add neon glows, grid perspectives, chrome

**C. Add Unexpected Spatial Element**

Quick wins:
- **Diagonal rotation**: `transform: rotate(-3deg)` on hero image
- **Overlap**: Negative margin between sections `-mt-16`
- **Asymmetry**: Change `grid-cols-2` to `grid-cols-[60%_40%]`
- **Viewport bleeding**: Elements escape container with `overflow-visible`

**D. Increase Animation Complexity**

Replace simple animations:
```tsx
// BEFORE (generic fade-in)
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
/>

// AFTER (orchestrated entrance)
<motion.div
  initial={{ opacity: 0, y: 50, scale: 0.95 }}
  animate={{ opacity: 1, y: 0, scale: 1 }}
  transition={{
    duration: 0.8,
    ease: [0.43, 0.13, 0.23, 0.96],  // Custom cubic-bezier
    delay: 0.2  // Part of staggered sequence
  }}
/>
```

---

### Issue: Animations Feel Scattered

**Symptom**: Many micro-interactions but no cohesive impact

**Diagnosis**:
- Animations triggered randomly throughout page
- No clear "moment" of visual impact
- User scrolls but nothing dramatic happens
- Hover effects feel disconnected

**Solution**: Consolidate into **high-impact moments**

**Strategy**:

**1. Page Load: Orchestrated Entrance**

Create a single choreographed sequence (3-5 elements):
```tsx
const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15  // 150ms between each child
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

<motion.div variants={containerVariants} initial="hidden" animate="show">
  <motion.h1 variants={itemVariants}>Heading</motion.h1>
  <motion.p variants={itemVariants}>Paragraph</motion.p>
  <motion.button variants={itemVariants}>CTA</motion.button>
</motion.div>
```

**2. Scroll: Parallax with Meaningful Depth**

Focus on 2-3 layers moving at different speeds:
```tsx
const { scrollYProgress } = useScroll({ target: ref });

// Background: 20% speed
const yBg = useTransform(scrollYProgress, [0, 1], ["0%", "20%"]);

// Midground (3D element): 40% speed
const yMid = useTransform(scrollYProgress, [0, 1], ["0%", "40%"]);

// Foreground (text): 60% speed
const yFg = useTransform(scrollYProgress, [0, 1], ["0%", "60%"]);
```

**3. Hover: Dramatic State Changes**

Make hover effects **obvious and delightful**:
```tsx
<motion.button
  whileHover={{
    scale: 1.05,
    boxShadow: "0 0 40px rgba(6, 182, 212, 0.6)",  // Cyan glow
    transition: { duration: 0.2 }
  }}
  whileTap={{ scale: 0.95 }}
>
  Get Started
</motion.button>
```

**4. Remove Scattered Micro-Interactions**

Delete:
- Simple opacity changes on scroll
- Tiny scale changes (1 → 1.02)
- Random fade-ins throughout page
- Disconnected hover effects

Keep only:
- **One** entrance animation sequence
- **One** scroll-triggered parallax effect
- **One** dramatic hover state per interactive element

---

## Resources

### Reference Materials (One Level Deep)

- **`reference/design-philosophy.md`** - Complete anti-convergence principles, case studies
- **`reference/animation-techniques.md`** - React Three Fiber + Framer Motion patterns with code
- **`reference/typography-guide.md`** - Font pairing strategies, variable fonts, avoid list
- **`reference/color-systems.md`** - Dominant palette strategies, CSS variable architecture
- **`reference/spatial-composition.md`** - Grid-breaking techniques, asymmetry, overlap
- **`reference/react-three-fiber-cookbook.md`** - Complete 3D patterns (molecule example)
- **`reference/anti-patterns.md`** - Explicit checklist of what to reject

### Validation Scripts

- **`scripts/validate_design.py`** - Detects generic fonts, colors, patterns
- **`scripts/dependency_check.sh`** - Verifies R3F, Framer Motion, Three.js installed

### Templates (Ready-to-Use Code)

- **`templates/hero-3d-parallax.tsx`** - Molecule hero section with Canvas + Framer Motion
- **`templates/glass-morphism.tsx`** - MeshTransmissionMaterial + Bloom setup
- **`templates/orchestrated-entrance.tsx`** - Staggered animation pattern
- **`templates/scroll-effects.tsx`** - useScroll + useTransform examples

### External Resources

- **React Three Fiber Docs**: https://docs.pmnd.rs/react-three-fiber
- **Drei Components**: https://github.com/pmndrs/drei
- **Framer Motion Docs**: https://www.framer.com/motion/
- **Design Philosophy Article**: https://www.claude.com/blog/improving-frontend-design-through-skills

---

## Final Checklist

Before completing this skill invocation:

1. ✅ Design philosophy documented (purpose, aesthetic, differentiator)
2. ✅ Anti-pattern checklist complete (explicit avoid list)
3. ✅ Typography distinctive (NO Inter/Roboto)
4. ✅ Color palette dominant (NO purple gradients)
5. ✅ Spatial composition intentional (breaks grid)
6. ✅ Animations high-impact (orchestrated or 3D)
7. ✅ `validate_design.py` passes with zero warnings
8. ✅ Performance: 60fps animations verified
9. ✅ Accessibility: WCAG AA compliance checked
10. ✅ **USER CONFIRMATION RECEIVED** - User has seen design and confirmed visual impact

**Remember**: Bold design requires continuous resistance against ANY convergence toward safety. **Think outside the box** at every step.
