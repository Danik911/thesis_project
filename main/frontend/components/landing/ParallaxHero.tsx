import { motion, useScroll, useTransform } from 'framer-motion';
import Image from 'next/image';
import Link from 'next/link';
import { useRef } from 'react';
import { useModal } from '@/context/ModalContext';
import { Canvas } from '@react-three/fiber';
import { Environment } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import Molecule from '../3d/Molecule';

export default function ParallaxHero() {
    const { openHowItWorks } = useModal();
    const ref = useRef(null);
    const { scrollYProgress } = useScroll({
        target: ref,
        offset: ["start start", "end start"]
    });

    const yText = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
    const yImage = useTransform(scrollYProgress, [0, 1], ["0%", "20%"]);
    const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

    return (
        <div ref={ref} className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
            {/* Background Elements */}
            <div className="absolute inset-0 z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px] animate-pulse-slow" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-indigo-600/20 rounded-full blur-[120px] animate-pulse-slow delay-1000" />
            </div>

            <Image
                src="https://images.unsplash.com/photo-1521737604893-d14cc237f11d?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2830&q=80&blend=111827&sat=-100&exp=15&blend-mode=multiply"
                alt=""
                fill
                className="absolute inset-0 -z-10 h-full w-full object-cover"
            />

            {/* 3D Molecules Layer - Single Canvas */}
            <div className="absolute inset-0 z-0">
                <Canvas camera={{ position: [0, 0, 10], fov: 45 }} gl={{ alpha: true }}>
                    {/* 3-Point Lighting Setup for Depth Perception */}
                    <ambientLight intensity={0.5} />
                    {/* Key light - main illumination */}
                    <pointLight position={[10, 10, 10]} intensity={2} color="#ffffff" />
                    {/* Fill light - cyan tinted to enhance mercury effect */}
                    <pointLight position={[-10, 5, -5]} intensity={0.8} color="#06b6d4" />
                    {/* Rim light - creates depth separation */}
                    <spotLight position={[0, 10, -10]} intensity={1.5} angle={0.3} />
                    <Environment preset="city" environmentIntensity={0.6} />

                    {/* Single Molecule - Top Left, closer to center */}
                    <Molecule scale={0.6} color="#60A5FA" position={[-3, 2, 0]} />

                    {/* Enhanced Bloom for Mercury Glow */}
                    <EffectComposer>
                        <Bloom
                            luminanceThreshold={0}
                            luminanceSmoothing={0.9}
                            intensity={3.0}
                            radius={1.0}
                        />
                    </EffectComposer>
                </Canvas>
            </div>

            <div className="container mx-auto px-6 relative z-10 grid lg:grid-cols-2 gap-12 items-center">
                {/* Text Content */}
                <motion.div
                    style={{ y: yText, opacity }}
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="text-center lg:text-left"
                >
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="inline-flex items-center rounded-full px-3 py-1 text-sm leading-6 text-blue-300 ring-1 ring-blue-500/30 bg-blue-900/20 mb-6"
                    >
                        <span>Now powered by DeepSeek V3.1</span>
                    </motion.div>

                    <h1 className="text-5xl lg:text-7xl font-bold tracking-tight text-white mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-100 to-blue-200">
                        Validation 4.0 <br />
                        <span className="text-blue-500">Reimagined.</span>
                    </h1>

                    <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto lg:mx-0 leading-relaxed">
                        Generate GAMP-driven OQ test suites in minutes.
                        Experience the future of pharmaceutical validation with AI-powered assurance.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
                        <Link
                            href="/generate"
                            className="rounded-full bg-blue-600 px-8 py-4 text-sm font-semibold text-white shadow-lg shadow-blue-500/25 hover:bg-blue-500 hover:scale-105 transition-all duration-300"
                        >
                            Get Started
                        </Link>
                        <button
                            onClick={openHowItWorks}
                            className="text-sm font-semibold leading-6 text-white hover:text-blue-300 transition-colors flex items-center gap-2 group"
                        >
                            How It Works
                            <span className="group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    </div>
                </motion.div>

                {/* 3D Asset */}
                <motion.div
                    style={{ y: yImage }}
                    initial={{ opacity: 0, scale: 0.8, rotate: -10 }}
                    animate={{ opacity: 1, scale: 1, rotate: 0 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="relative h-[500px] w-full hidden lg:block"
                >
                    {/* Placeholder for the generated 3D asset - assuming it will be placed in public/images */}
                    <div className="absolute inset-0 flex items-center justify-center overflow-visible group">
                        {/* We will replace this with the actual image later */}
                        <div className="absolute inset-0 bg-[url('/hero-3d-asset.png')] bg-contain bg-center bg-no-repeat animate-float" />

                        {/* Floating Elements for depth */}
                        <motion.div
                            animate={{ y: [0, -20, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute top-10 right-10 w-20 h-20 bg-blue-400/20 rounded-full blur-xl"
                        />
                        <motion.div
                            animate={{ y: [0, 30, 0] }}
                            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                            className="absolute bottom-20 left-10 w-32 h-32 bg-indigo-400/20 rounded-full blur-xl"
                        />
                    </div>
                </motion.div>
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
