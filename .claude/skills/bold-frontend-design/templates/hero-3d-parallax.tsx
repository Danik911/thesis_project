/**
 * Hero Section with 3D Parallax
 *
 * Features:
 * - 3D molecule visualization with glass effect + Bloom
 * - Framer Motion parallax scrolling
 * - Orchestrated entrance animations
 * - Responsive design
 *
 * Dependencies:
 * - @react-three/fiber
 * - @react-three/drei
 * - @react-three/postprocessing
 * - framer-motion
 * - three
 */

import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { Environment } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import Molecule from '../3d/Molecule';  // Adjust path as needed

export default function Hero3DParallax() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"]
  });

  const yText = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <div ref={ref} className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Background Gradient Blobs */}
      <div className="absolute inset-0 z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/20 rounded-full blur-[120px] animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* 3D Molecule Layer */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 10], fov: 45 }} gl={{ alpha: true }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} intensity={1.5} />
          <Environment preset="city" environmentIntensity={0.8} />

          {/* Glass molecule with bloom */}
          <Molecule scale={0.6} color="#60A5FA" position={[-3, 2, 0]} />

          {/* Bloom Post-Processing */}
          <EffectComposer>
            <Bloom
              luminanceThreshold={0}
              luminanceSmoothing={0.9}
              intensity={2.5}
              radius={0.8}
            />
          </EffectComposer>
        </Canvas>
      </div>

      {/* Content Layer with Parallax */}
      <div className="container mx-auto px-6 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        {/* Text Content - Orchestrated Entrance */}
        <motion.div
          style={{ y: yText, opacity }}
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center lg:text-left"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center rounded-full px-3 py-1 text-sm leading-6 text-blue-300 ring-1 ring-blue-500/30 bg-blue-900/20 mb-6"
          >
            <span>Now powered by AI</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="text-5xl lg:text-7xl font-bold tracking-tight text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-blue-200"
          >
            Your Product <br />
            <span className="text-blue-500">Reimagined.</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed"
          >
            Transform your workflow with AI-powered innovation. Experience the future today.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4"
          >
            <motion.a
              href="/get-started"
              className="rounded-full bg-blue-600 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 hover:bg-blue-500 transition-all duration-300"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Get Started
            </motion.a>

            <button className="text-sm font-semibold leading-6 text-white hover:text-blue-300 transition-colors flex items-center gap-2 group">
              Learn More
              <span className="group-hover:translate-x-1 transition-transform">→</span>
            </button>
          </motion.div>
        </motion.div>

        {/* Spacer for molecule (molecule is positioned absolutely) */}
        <div className="hidden lg:block" />
      </div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 1 }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 text-gray-400"
      >
        <span className="text-xs uppercase tracking-widest">Scroll</span>
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="w-1 h-12 rounded-full bg-gradient-to-b from-blue-500 to-transparent"
        />
      </motion.div>
    </div>
  );
}

/**
 * Usage:
 *
 * 1. Import this component in your page
 * 2. Ensure you have a Molecule component at ../3d/Molecule.tsx
 * 3. Add pulse animation to your Tailwind config:
 *
 * // tailwind.config.js
 * module.exports = {
 *   theme: {
 *     extend: {
 *       animation: {
 *         'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
 *       },
 *     },
 *   },
 * };
 *
 * 4. Customize:
 * - Change Molecule color prop
 * - Adjust text content
 * - Modify gradient colors
 * - Update CTA links
 */
