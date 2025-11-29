import Head from 'next/head';
import Link from 'next/link';
import Layout from '@/components/Layout';
import { CheckCircleIcon, ClockIcon, CurrencyDollarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import ParallaxHero from '@/components/landing/ParallaxHero';
import AnimatedSection from '@/components/landing/AnimatedSection';
import { Canvas } from '@react-three/fiber';
import { Environment } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import Molecule from '@/components/3d/Molecule';
import { motion } from 'framer-motion';

export default function LandingPage() {
  return (
    <>
      <Head>
        <title>PharmaGen AI - Automated CSV & OQ Test Generation</title>
        <meta name="description" content="Generate GAMP driven OQ test suites in minutes using AI. Reduce validation costs by 90%." />
      </Head>

      <Layout>
        <ParallaxHero />

        {/* Pain Points Section */}
        <div className="bg-slate-900/50 py-24 lg:py-32 relative overflow-hidden">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,theme(colors.indigo.900),transparent)] opacity-20" />

          {/* Added Gradient Blobs for consistency */}
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[100px]" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[100px]" />

          {/* 3D Molecules Layer */}
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

              {/* Left Molecule */}
              <Molecule scale={0.5} color="#F87171" position={[-7, 0, 0]} />

              {/* Right Molecule */}
              <Molecule scale={0.5} color="#60A5FA" position={[7, 2, 0]} />

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

          <div className="mx-auto max-w-7xl px-6 lg:px-8 relative z-10 pointer-events-none">
            <div className="pointer-events-auto">
              <AnimatedSection className="mx-auto max-w-2xl lg:text-center">
                <h2 className="text-base font-semibold leading-7 text-blue-400">The Manual CSV Nightmare</h2>
                <p className="mt-2 text-6xl lg:text-7xl font-black tracking-tight text-white leading-tight">
                  Why are you still writing tests by hand?
                </p>
                <p className="mt-12 text-2xl lg:text-3xl leading-relaxed font-medium text-gray-300">
                  Traditional validation is slow, expensive, and prone to human error. It&apos;s time for Validation 4.0.
                </p>
              </AnimatedSection>

              <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
                {/* Asymmetric 60/40 Grid Layout - Bold Transformation */}
                <div className="grid grid-cols-1 lg:grid-cols-[60%_40%] gap-8 relative">
                  {/* Featured Card - Left 60% with elevation */}
                  <AnimatedSection delay={0.2} className="relative z-20 transform lg:-mr-12">
                    <div className="card p-10 shadow-2xl shadow-red-500/20 border-2 border-red-500/30 hover:shadow-red-500/40 transition-all duration-300">
                      <dt className="flex items-center gap-x-4 text-4xl lg:text-5xl font-black leading-tight text-white">
                        <ClockIcon className="h-12 w-12 flex-none text-red-400" aria-hidden="true" />
                        Weeks of Delay
                      </dt>
                      <dd className="mt-8 text-xl lg:text-2xl leading-relaxed text-gray-300 font-medium">
                        Manual protocol writing bottlenecks project timelines. A single system can take 2-3 weeks to validate manually.
                      </dd>
                    </div>
                  </AnimatedSection>

                  {/* Stacked Cards - Right 40% */}
                  <div className="space-y-8 relative z-10">
                    <AnimatedSection delay={0.4} className="flex flex-col">
                      <div className="card p-8 hover:shadow-xl hover:shadow-red-500/10 transition-all duration-300">
                        <dt className="flex items-center gap-x-3 text-3xl font-black leading-tight text-white">
                          <CurrencyDollarIcon className="h-8 w-8 flex-none text-red-400" aria-hidden="true" />
                          High Costs
                        </dt>
                        <dd className="mt-6 text-xl leading-relaxed text-gray-300 font-medium">
                          Validation consultants cost $150+/hr. We reduce generation costs to pennies per test suite.
                        </dd>
                      </div>
                    </AnimatedSection>

                    <AnimatedSection delay={0.6} className="flex flex-col">
                      <div className="card p-8 hover:shadow-xl hover:shadow-red-500/10 transition-all duration-300">
                        <dt className="flex items-center gap-x-3 text-3xl font-black leading-tight text-white">
                          <ShieldCheckIcon className="h-8 w-8 flex-none text-red-400" aria-hidden="true" />
                          Compliance Risks
                        </dt>
                        <dd className="mt-6 text-xl leading-relaxed text-gray-300 font-medium">
                          Manual scripts often miss requirements or lack traceability, leading to painful audit findings.
                        </dd>
                      </div>
                    </AnimatedSection>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Solution Section */}
        <div className="py-24 lg:py-32 relative overflow-hidden">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_bottom,theme(colors.blue.900),transparent)] opacity-20" />
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <AnimatedSection className="mx-auto max-w-2xl lg:text-center">
              <h2 className="text-base font-semibold leading-7 text-blue-400">Validation 4.0</h2>
              <p className="mt-2 text-6xl lg:text-8xl font-black tracking-tight text-white leading-tight">
                AI-Driven Computer Software Assurance (CSA)
              </p>
              <p className="mt-12 text-3xl leading-relaxed font-medium text-gray-300">
                Shift from documentation-heavy validation to critical thinking and automated assurance.
              </p>
            </AnimatedSection>

            <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
              {/* Diagonal Z-Pattern Flow - Staggered Elevation */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
                {/* Card 1 - Top Left, Normal Position */}
                <AnimatedSection delay={0.2} className="flex flex-col">
                  <div className="card p-8 hover:shadow-xl hover:shadow-green-500/20 transition-all duration-300">
                    <dt className="flex items-center gap-x-3 text-4xl font-black leading-tight text-white">
                      <CheckCircleIcon className="h-10 w-10 flex-none text-green-400" aria-hidden="true" />
                      95% Faster
                    </dt>
                    <dd className="mt-6 text-xl leading-relaxed text-gray-300 font-medium">
                      Generate complete, compliant OQ test suites in 8-12 minutes.
                    </dd>
                  </div>
                </AnimatedSection>

                {/* Card 2 - Center, Elevated + Rotated */}
                <AnimatedSection delay={0.4} className="flex flex-col transform lg:translate-y-8 lg:-rotate-1">
                  <div className="card p-8 shadow-lg shadow-green-500/10 hover:shadow-xl hover:shadow-green-500/30 transition-all duration-300">
                    <dt className="flex items-center gap-x-3 text-4xl font-black leading-tight text-white">
                      <CheckCircleIcon className="h-10 w-10 flex-none text-green-400" aria-hidden="true" />
                      Audit Ready
                    </dt>
                    <dd className="mt-6 text-xl leading-relaxed text-gray-300 font-medium">
                      Full ALCOA+ data integrity, electronic signatures (21 CFR Part 11), and immutable audit trails.
                    </dd>
                  </div>
                </AnimatedSection>

                {/* Card 3 - Bottom Right, More Elevated + Rotated */}
                <AnimatedSection delay={0.6} className="flex flex-col transform lg:translate-y-16 lg:rotate-1">
                  <div className="card p-8 shadow-xl shadow-green-500/15 hover:shadow-2xl hover:shadow-green-500/40 transition-all duration-300">
                    <dt className="flex items-center gap-x-3 text-4xl font-black leading-tight text-white">
                      <CheckCircleIcon className="h-10 w-10 flex-none text-green-400" aria-hidden="true" />
                      Risk-Based
                    </dt>
                    <dd className="mt-6 text-xl leading-relaxed text-gray-300 font-medium">
                      Automatic GAMP 5 categorization ensures you focus testing efforts where risk is highest.
                    </dd>
                  </div>
                </AnimatedSection>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section - Enhanced with Gradient Blobs */}
        <AnimatedSection className="relative isolate mt-32 px-6 py-32 sm:mt-56 sm:px-8 overflow-hidden">
          {/* Animated Gradient Blobs Background */}
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />

          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,theme(colors.indigo.100),white)] opacity-20" />
          <div className="absolute inset-y-0 right-1/2 -z-10 mr-16 w-[200%] origin-bottom-left skew-x-[-30deg] bg-slate-900 shadow-xl shadow-indigo-600/10 ring-1 ring-indigo-50 sm:mr-28 lg:mr-0 xl:mr-16 xl:origin-center" />

          <div className="mx-auto max-w-2xl text-center relative z-10">
            {/* Staggered Entrance Animation */}
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0 }}
              className="text-5xl lg:text-6xl font-black tracking-tight text-white leading-tight"
            >
              Ready to modernize your validation?
              <br />
              <span className="text-cyan-400">Start generating tests today.</span>
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.15 }}
              className="mx-auto mt-8 max-w-xl text-xl lg:text-2xl leading-relaxed text-gray-300 font-medium"
            >
              Join the Validation 4.0 revolution. Secure, compliant, and efficient.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="mt-12 flex items-center justify-center gap-x-6"
            >
              <Link
                href="/generate"
                className="group relative rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 px-10 py-5 text-xl font-bold text-white shadow-2xl shadow-cyan-500/50 hover:from-cyan-400 hover:to-blue-500 hover:shadow-cyan-400/70 transition-all duration-300 hover:scale-105"
              >
                <span className="relative z-10 flex items-center gap-2">
                  Get Started
                  <motion.span
                    animate={{ x: [0, 5, 0] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  >
                    →
                  </motion.span>
                </span>
              </Link>
            </motion.div>

            {/* Trust Indicator Badges */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: 0.45 }}
              className="mt-12 flex flex-wrap items-center justify-center gap-4"
            >
              <div className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-green-400 ring-1 ring-green-500/30 bg-green-900/20">
                <CheckCircleIcon className="h-5 w-5" aria-hidden="true" />
                GAMP-5 Compliant
              </div>
              <div className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-green-400 ring-1 ring-green-500/30 bg-green-900/20">
                <CheckCircleIcon className="h-5 w-5" aria-hidden="true" />
                21 CFR Part 11 Ready
              </div>
              <div className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium text-green-400 ring-1 ring-green-500/30 bg-green-900/20">
                <CheckCircleIcon className="h-5 w-5" aria-hidden="true" />
                ALCOA+ Validated
              </div>
            </motion.div>
          </div>
        </AnimatedSection>
      </Layout>
    </>
  );
}
