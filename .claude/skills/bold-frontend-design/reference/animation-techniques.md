# Animation Techniques: React Three Fiber + Framer Motion

## Overview

This guide documents **production-tested** animation patterns for creating bold, memorable frontend experiences using:

- **React Three Fiber** (R3F) - 3D graphics and WebGL
- **Framer Motion** - 2D animations and gestures
- **@react-three/drei** - Helper components
- **@react-three/postprocessing** - Visual effects (Bloom, etc.)

All patterns are from **real implementations** that have been validated for performance (60fps) and visual impact.

---

## React Three Fiber Patterns

### Pattern 1: Glass Material with Bloom Glow

**Use Case**: Creating ethereal, glowing 3D objects (molecules, abstract shapes)

**Visual Effect**: Transparent glass spheres with rainbow refraction + soft glow

**Dependencies**:
```json
{
  "@react-three/fiber": "^8.18.0",
  "@react-three/drei": "^9.122.0",
  "@react-three/postprocessing": "^2.16.0",
  "three": "^0.181.2"
}
```

**Implementation**:

```tsx
import { Canvas } from '@react-three/fiber';
import { MeshTransmissionMaterial, Environment, Float, Sphere } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';

export default function GlassMolecule() {
  return (
    <Canvas camera={{ position: [0, 0, 10], fov: 45 }} gl={{ alpha: true }}>
      {/* Lighting Setup */}
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1.5} />
      <Environment preset="city" environmentIntensity={0.8} />

      {/* Glowing Glass Sphere */}
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <Sphere args={[1, 32, 32]} position={[0, 0, 0]}>
          <MeshTransmissionMaterial
            // Glass properties
            transmission={1}              // Full transparency (0-1)
            thickness={0.3}               // Refraction depth
            roughness={0}                 // 0 = polished, 1 = frosted
            ior={1.3}                     // Index of refraction (glass ~1.5)
            chromaticAberration={0.02}    // Rainbow edge effect

            // Color & glow
            color="#06b6d4"               // Base color (cyan)
            emissive="#06b6d4"            // Emissive color (for Bloom)
            emissiveIntensity={0.15}      // Glow strength

            // Additional properties
            backside={true}               // Render both sides
            attenuationDistance={0.5}     // Light absorption distance
            attenuationColor="#ffffff"    // Absorbed light color
          />
        </Sphere>
      </Float>

      {/* Bloom Post-Processing */}
      <EffectComposer>
        <Bloom
          luminanceThreshold={0}          // Glow all bright objects
          luminanceSmoothing={0.9}        // Smooth glow transitions
          intensity={2.5}                 // Glow strength (0-5)
          radius={0.8}                    // Blur spread (0-1)
        />
      </EffectComposer>
    </Canvas>
  );
}
```

**Key Parameters**:

| Property | Value | Effect |
|----------|-------|--------|
| `transmission` | 0 | Opaque |
| `transmission` | 0.5 | Semi-transparent |
| `transmission` | 1 | Fully transparent (glass) |
| `roughness` | 0 | Polished, clear reflections |
| `roughness` | 0.5 | Slightly frosted |
| `roughness` | 1 | Fully frosted (matte) |
| `ior` | 1.0 | No refraction |
| `ior` | 1.3-1.5 | Glass-like refraction |
| `ior` | 2.4 | Diamond-like refraction |
| `chromaticAberration` | 0 | No color separation |
| `chromaticAberration` | 0.02-0.05 | Rainbow edge effect |

**Performance Notes**:
- MeshTransmissionMaterial is GPU-intensive (uses screen-space refraction)
- Limit to 3-5 objects per scene for 60fps
- Use `args={[size, 16, 16]}` (lower segments) on mobile

---

### Pattern 2: Continuous Rotation with Smooth Interactions

**Use Case**: Rotating 3D objects that respond to hover/click

**Visual Effect**: Smooth rotation that speeds up on hover

**Implementation**:

```tsx
import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function RotatingMolecule() {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHover] = useState(false);
  const rotationSpeed = useRef(1);
  const currentScale = useRef(1);

  useFrame((state, delta) => {
    if (groupRef.current) {
      // Smoothly interpolate rotation speed
      const targetSpeed = hovered ? 3 : 1;
      rotationSpeed.current = THREE.MathUtils.lerp(
        rotationSpeed.current,
        targetSpeed,
        0.05  // Smoothing factor (0-1, lower = smoother)
      );

      // Apply multi-axis rotation
      groupRef.current.rotation.y += delta * 0.2 * rotationSpeed.current;
      groupRef.current.rotation.x += delta * 0.1 * rotationSpeed.current;
      groupRef.current.rotation.z += delta * 0.05 * rotationSpeed.current;

      // Smoothly interpolate scale
      const targetScale = hovered ? 1.2 : 1;
      currentScale.current = THREE.MathUtils.lerp(
        currentScale.current,
        targetScale,
        0.1  // Scale changes faster than rotation
      );
      groupRef.current.scale.setScalar(currentScale.current);
    }
  });

  return (
    <group
      ref={groupRef}
      onPointerOver={() => setHover(true)}
      onPointerOut={() => setHover(false)}
    >
      {/* Your 3D objects */}
      <mesh>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial color="#60A5FA" />
      </mesh>
    </group>
  );
}
```

**Key Concepts**:

1. **useFrame Hook**: Runs on every frame (60fps)
   ```tsx
   useFrame((state, delta) => {
     // state: Clock, camera, scene, etc.
     // delta: Time since last frame (for frame-rate independent animation)
   });
   ```

2. **THREE.MathUtils.lerp**: Smooth interpolation
   ```tsx
   lerp(current, target, alpha)
   // alpha: 0.05 = slow transition, 0.5 = medium, 1.0 = instant
   ```

3. **Multi-Axis Rotation**: Creates natural movement
   - Y-axis (vertical): Primary rotation
   - X-axis (horizontal): Secondary tilt
   - Z-axis (roll): Tertiary wobble

**Performance**: 60fps for 10-20 rotating objects

---

### Pattern 3: Deterministic 3D Structures

**Use Case**: Creating stable, reproducible molecular/chemical structures

**Problem**: Random positioning (`Math.random()`) creates non-reproducible, chaotic structures

**Solution**: Deterministic coordinate arrays

**Implementation**:

```tsx
// Define structure once (outside component)
const MOLECULAR_STRUCTURE = [
  // Core atoms
  {
    position: [-0.8, 0, 0] as [number, number, number],
    size: 0.6,
    element: 'C',
    color: '#909090',
    parent: null
  },
  {
    position: [0.8, 0, 0] as [number, number, number],
    size: 0.6,
    element: 'C',
    color: '#909090',
    parent: [-0.8, 0, 0] as [number, number, number]  // Connect to first atom
  },

  // Peripheral atoms (tetrahedral-inspired)
  {
    position: [-1.8, 1.2, 0.6] as [number, number, number],
    size: 0.35,
    element: 'N',
    color: '#3050F8',
    parent: [-0.8, 0, 0] as [number, number, number]
  },
  {
    position: [1.8, 1.2, 0.6] as [number, number, number],
    size: 0.35,
    element: 'N',
    color: '#3050F8',
    parent: [0.8, 0, 0] as [number, number, number]
  },
  // ... more atoms
];

function Molecule() {
  const atoms = useMemo(() => MOLECULAR_STRUCTURE, []);

  return (
    <group>
      {atoms.map((atom, i) => (
        <group key={i}>
          <Sphere args={[atom.size, 32, 32]} position={atom.position}>
            <MeshTransmissionMaterial color={atom.color} {...glassProps} />
          </Sphere>

          {/* Bond to parent */}
          {atom.parent && (
            <Bond start={atom.parent} end={atom.position} color={atom.color} />
          )}
        </group>
      ))}
    </group>
  );
}
```

**Benefits**:
- ✅ Reproducible (same structure every time)
- ✅ Scientifically accurate (proper bond angles)
- ✅ Performance (no recalculation on render)
- ✅ Maintainable (easy to adjust positions)

---

### Pattern 4: Bond/Connection Visualization

**Use Case**: Connecting spheres (atoms) with cylinders (bonds)

**Visual Effect**: Dynamic cylinders that calculate position/rotation to connect two points

**Implementation**:

```tsx
function Bond({ start, end, color }: {
  start: [number, number, number];
  end: [number, number, number];
  color: string;
}) {
  // Calculate bond geometry
  const startVec = new THREE.Vector3(...start);
  const endVec = new THREE.Vector3(...end);
  const direction = new THREE.Vector3().subVectors(endVec, startVec);
  const length = direction.length();
  const midpoint = new THREE.Vector3().addVectors(startVec, endVec).multiplyScalar(0.5);

  // Calculate rotation to align cylinder with direction
  const quaternion = new THREE.Quaternion();
  quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),  // Cylinder default orientation (Y-up)
    direction.normalize()         // Target direction
  );
  const rotation = new THREE.Euler().setFromQuaternion(quaternion);

  return (
    <Cylinder
      args={[0.12, 0.12, length, 16]}  // [radiusTop, radiusBottom, height, segments]
      position={[midpoint.x, midpoint.y, midpoint.z]}
      rotation={[rotation.x, rotation.y, rotation.z]}
    >
      <MeshTransmissionMaterial
        transmission={0.9}
        thickness={0.2}
        roughness={0.1}
        ior={1.3}
        color={color}
        emissive={color}
        emissiveIntensity={0.1}
      />
    </Cylinder>
  );
}
```

**Math Breakdown**:

1. **Vector Subtraction**: Get direction from start to end
   ```tsx
   direction = end - start
   ```

2. **Length Calculation**: Distance between points
   ```tsx
   length = |direction| = sqrt(x² + y² + z²)
   ```

3. **Midpoint**: Average of start and end
   ```tsx
   midpoint = (start + end) / 2
   ```

4. **Quaternion Rotation**: Align cylinder with direction
   ```tsx
   // Default cylinder points up (Y-axis)
   // Quaternion rotates it to point toward direction
   ```

---

### Pattern 5: Environment Lighting

**Use Case**: Quick, realistic lighting without manual light setup

**Visual Effect**: HDRI-based ambient lighting with reflections

**Implementation**:

```tsx
import { Environment } from '@react-three/drei';

<Canvas>
  {/* Basic lights */}
  <ambientLight intensity={0.5} />
  <pointLight position={[10, 10, 10]} intensity={1.5} />

  {/* Environment preset */}
  <Environment
    preset="city"              // Options: sunset, dawn, night, warehouse, forest, apartment, studio, city, park, lobby
    environmentIntensity={0.8}  // Intensity multiplier (0-1)
  />

  {/* Your 3D objects */}
</Canvas>
```

**Presets**:
| Preset | Mood | Use Case |
|--------|------|----------|
| `sunset` | Warm, golden | Luxury, organic aesthetics |
| `city` | Cool, urban | Tech, futuristic designs |
| `studio` | Neutral, bright | Product showcases |
| `night` | Dark, dramatic | Gaming, cinematic |
| `warehouse` | Industrial | Brutalist, raw aesthetics |

**Custom HDRI**:
```tsx
<Environment files="/path/to/hdri.hdr" />
```

---

## Framer Motion Patterns

### Pattern 6: Orchestrated Entrance Animations

**Use Case**: Choreographed reveal sequence on page load

**Visual Effect**: Staggered appearance of elements (heading → paragraph → button)

**Implementation**:

```tsx
import { motion } from 'framer-motion';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,  // 150ms between each child
      delayChildren: 0.3      // Wait 300ms before first child
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.6,
      ease: [0.43, 0.13, 0.23, 0.96]  // Custom cubic-bezier
    }
  }
};

export default function HeroSection() {
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
    >
      <motion.h1 variants={itemVariants}>
        Validation 4.0 Reimagined
      </motion.h1>

      <motion.p variants={itemVariants}>
        Generate GAMP-driven test suites in minutes.
      </motion.p>

      <motion.button variants={itemVariants}>
        Get Started
      </motion.button>
    </motion.div>
  );
}
```

**Key Parameters**:

- **staggerChildren**: Delay between each child animation
  - `0.05` = Fast sequence (50ms)
  - `0.15` = Medium sequence (150ms)
  - `0.3` = Slow sequence (300ms)

- **delayChildren**: Wait before starting sequence
  - Useful for delaying entrance after page load

- **Custom Easing**: `ease: [0.43, 0.13, 0.23, 0.96]`
  - Creates sophisticated, non-linear motion
  - Generator: https://cubic-bezier.com/

**Visual Timeline**:
```
0ms:    Container fades in
300ms:  Delay complete
300ms:  H1 starts animating (opacity, y, scale)
450ms:  P starts animating (150ms after H1)
600ms:  Button starts animating (150ms after P)
```

---

### Pattern 7: Scroll-Triggered Parallax

**Use Case**: Elements move at different speeds on scroll

**Visual Effect**: Depth and dimensionality through layered movement

**Implementation**:

```tsx
import { useRef } from 'react';
import { useScroll, useTransform, motion } from 'framer-motion';

export default function ParallaxSection() {
  const ref = useRef(null);

  // Track scroll progress of this section
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"]
    // "start start" = section top hits viewport top
    // "end start" = section bottom hits viewport top
  });

  // Transform scroll progress to Y positions
  const yBackground = useTransform(scrollYProgress, [0, 1], ["0%", "20%"]);
  const yMidground = useTransform(scrollYProgress, [0, 1], ["0%", "40%"]);
  const yForeground = useTransform(scrollYProgress, [0, 1], ["0%", "60%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <section ref={ref} className="relative min-h-screen">
      {/* Background Layer - Slowest */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-blue-900 to-slate-900"
        style={{ y: yBackground }}
      />

      {/* Midground Layer - Medium Speed */}
      <motion.div
        className="absolute inset-0"
        style={{ y: yMidground }}
      >
        <Canvas>
          {/* 3D elements move at 40% speed */}
        </Canvas>
      </motion.div>

      {/* Foreground Layer - Fastest */}
      <motion.div
        className="relative z-10"
        style={{ y: yForeground, opacity }}
      >
        <h1>Text moves at 60% speed and fades out</h1>
      </motion.div>
    </section>
  );
}
```

**Scroll Offset Explained**:

```tsx
offset: ["start start", "end start"]
//       [trigger,       completion]
```

**Common Offset Patterns**:
| Offset | Effect |
|--------|--------|
| `["start end", "end start"]` | Animates entire time section is in viewport |
| `["start start", "end start"]` | Starts when section enters viewport top |
| `["start center", "end center"]` | Animates around viewport center |
| `["start end", "start start"]` | Quick animation as section enters |

**Transform Ranges**:
```tsx
useTransform(scrollYProgress, [0, 1], ["0%", "60%"])
//                             input    output
```

- **Input**: `[0, 1]` = full scroll range (0% to 100%)
- **Output**: `["0%", "60%"]` = Y position values

**Parallax Speed Hierarchy**:
- Background: 20% (slowest, creates depth)
- Midground: 40% (medium, main focus)
- Foreground: 60% (fastest, creates motion)

---

### Pattern 8: Infinite Loop Animations

**Use Case**: Continuous floating/pulsing elements

**Visual Effect**: Gentle, organic movement that never stops

**Implementation**:

```tsx
<motion.div
  animate={{
    y: [0, -20, 0],           // Keyframes: start, peak, return
    scale: [1, 1.05, 1],      // Subtle scale pulse
    rotate: [0, 5, 0]         // Gentle rotation
  }}
  transition={{
    duration: 4,              // Full cycle time (seconds)
    repeat: Infinity,         // Loop forever
    ease: "easeInOut",        // Smooth acceleration/deceleration
    delay: 0.5                // Stagger if multiple elements
  }}
>
  Floating Element
</motion.div>
```

**Keyframe Patterns**:

**Smooth Loop** (easeInOut):
```tsx
y: [0, -20, 0]  // Up and down
transition: { ease: "easeInOut" }
```

**Springy Loop** (anticipation):
```tsx
y: [0, -5, -20, 0]  // Small dip → big rise → return
transition: { ease: [0.65, 0, 0.35, 1] }
```

**Multiple Properties**:
```tsx
animate={{
  y: [0, -20, 0],
  x: [0, 10, 0],
  rotate: [0, 5, -5, 0],
  scale: [1, 1.02, 1]
}}
```

**Staggered Timing** (multiple elements):
```tsx
{floatingElements.map((el, i) => (
  <motion.div
    key={i}
    animate={{ y: [0, -20, 0] }}
    transition={{
      duration: 4,
      repeat: Infinity,
      delay: i * 0.3  // Each element delayed by 300ms
    }}
  />
))}
```

---

### Pattern 9: Gesture-Based Interactions

**Use Case**: Hover/tap/drag interactions

**Visual Effect**: Responsive feedback to user input

**Implementation**:

```tsx
<motion.button
  // Hover state
  whileHover={{
    scale: 1.05,
    boxShadow: "0 0 40px rgba(6, 182, 212, 0.6)",
    transition: { duration: 0.2 }
  }}

  // Active/pressed state
  whileTap={{
    scale: 0.95
  }}

  // Focus state (keyboard)
  whileFocus={{
    outline: "2px solid #06b6d4",
    outlineOffset: "4px"
  }}
>
  Interactive Button
</motion.button>
```

**Advanced Hover Effects**:

```tsx
const [isHovered, setIsHovered] = useState(false);

<motion.div
  onHoverStart={() => setIsHovered(true)}
  onHoverEnd={() => setIsHovered(false)}
  animate={{
    backgroundColor: isHovered ? "#06b6d4" : "#ffffff",
    color: isHovered ? "#ffffff" : "#000000"
  }}
  transition={{ duration: 0.3 }}
>
  <motion.span
    animate={{
      x: isHovered ? 10 : 0,
      opacity: isHovered ? 1 : 0.7
    }}
  >
    → Hover Me
  </motion.span>
</motion.div>
```

**Drag Interaction**:

```tsx
<motion.div
  drag                         // Enable dragging
  dragConstraints={{
    top: -50,
    left: -50,
    right: 50,
    bottom: 50
  }}
  dragElastic={0.2}           // Rubber-band effect (0-1)
  dragTransition={{
    bounceStiffness: 600,
    bounceDamping: 20
  }}
  whileDrag={{
    scale: 1.1,
    cursor: "grabbing"
  }}
>
  Draggable Element
</motion.div>
```

---

### Pattern 10: Scroll Indicators

**Use Case**: Animated arrow/bar prompting user to scroll

**Visual Effect**: Bouncing arrow or pulsing gradient

**Implementation**:

```tsx
<div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center">
  <span className="text-xs uppercase tracking-widest text-gray-400">Scroll</span>

  <motion.div
    animate={{ y: [0, 10, 0] }}
    transition={{
      duration: 1.5,
      repeat: Infinity,
      ease: "easeInOut"
    }}
    className="mt-2 w-1 h-12 rounded-full bg-gradient-to-b from-blue-500 to-transparent"
  />
</div>
```

**Alternative: Animated Arrow**:

```tsx
<motion.svg
  width="24"
  height="24"
  viewBox="0 0 24 24"
  animate={{ y: [0, 8, 0] }}
  transition={{
    duration: 1.2,
    repeat: Infinity,
    ease: [0.65, 0, 0.35, 1]
  }}
>
  <path
    d="M12 4L12 20M12 20L6 14M12 20L18 14"
    stroke="currentColor"
    strokeWidth="2"
    fill="none"
  />
</motion.svg>
```

---

## Combining R3F + Framer Motion

### Pattern 11: 3D Background with 2D Overlay

**Use Case**: 3D Canvas as background, Framer Motion for foreground content

**Architecture**:

```tsx
<section className="relative min-h-screen">
  {/* Layer 1: 3D Background (z-index: 0) */}
  <div className="absolute inset-0 z-0">
    <Canvas camera={{ position: [0, 0, 10], fov: 45 }} gl={{ alpha: true }}>
      <ambientLight intensity={0.5} />
      <Float speed={2}>
        <Molecule />
      </Float>
      <EffectComposer>
        <Bloom intensity={2.5} />
      </EffectComposer>
    </Canvas>
  </div>

  {/* Layer 2: 2D Content (z-index: 10) */}
  <motion.div
    className="relative z-10 container mx-auto px-6"
    initial={{ opacity: 0, y: 50 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.8, delay: 0.3 }}
  >
    <h1>Overlaid Text Content</h1>
    <p>Sits on top of 3D scene</p>
  </motion.div>
</section>
```

**Key Techniques**:
1. **Canvas with alpha**: `gl={{ alpha: true }}` makes background transparent
2. **Absolute positioning**: Canvas fills parent container
3. **Z-index layering**: 3D (z-0) behind 2D content (z-10)
4. **Framer Motion orchestration**: 2D content animates independently

---

## Performance Optimization

### Technique 1: Reduce Geometry Complexity

**Problem**: High-poly models cause FPS drops

**Solution**: Lower segment count on spheres/cylinders

```tsx
// Desktop (high quality)
<sphereGeometry args={[1, 32, 32]} />  // 1024 triangles

// Mobile (optimized)
<sphereGeometry args={[1, 16, 16]} />  // 256 triangles (4x fewer)
```

**Conditional Rendering**:
```tsx
const isMobile = window.innerWidth < 768;

<sphereGeometry args={[1, isMobile ? 16 : 32, isMobile ? 16 : 32]} />
```

---

### Technique 2: Disable Effects on Mobile

**Problem**: Bloom/post-processing is GPU-intensive on mobile

**Solution**: Conditional EffectComposer

```tsx
const isMobile = window.innerWidth < 768;

<Canvas>
  <Molecule />

  {!isMobile && (
    <EffectComposer>
      <Bloom intensity={2.5} />
    </EffectComposer>
  )}
</Canvas>
```

---

### Technique 3: Respect Reduced Motion Preference

**Problem**: Users with vestibular disorders need reduced motion

**Solution**: Check `prefers-reduced-motion` media query

```tsx
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

<motion.div
  animate={{ opacity: 1, y: 0 }}
  transition={{
    duration: prefersReducedMotion ? 0 : 0.8,  // Instant if reduced motion
    delay: prefersReducedMotion ? 0 : 0.3
  }}
>
  Content
</motion.div>
```

**Global Hook**:
```tsx
function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}
```

---

## Quick Reference

### React Three Fiber Essentials

```tsx
import { Canvas, useFrame } from '@react-three/fiber';
import { MeshTransmissionMaterial, Environment, Float, Sphere, Cylinder } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import * as THREE from 'three';
```

### Framer Motion Essentials

```tsx
import { motion, useScroll, useTransform } from 'framer-motion';
```

### Common Imports

```tsx
import { useRef, useState, useMemo } from 'react';
```

---

**All patterns in this guide are production-tested and optimized for 60fps performance.**
