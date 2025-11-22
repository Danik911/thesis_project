import Head from 'next/head';
import Layout from '@/components/Layout';
import { CheckCircleIcon, ClockIcon, CurrencyDollarIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import ParallaxHero from '@/components/landing/ParallaxHero';
import AnimatedSection from '@/components/landing/AnimatedSection';

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
        <div className="bg-slate-900/50 py-16 sm:py-24 relative overflow-hidden">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,theme(colors.indigo.900),transparent)] opacity-20" />
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <AnimatedSection className="mx-auto max-w-2xl lg:text-center">
              <h2 className="text-base font-semibold leading-7 text-blue-400">The Manual CSV Nightmare</h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Why are you still writing tests by hand?
              </p>
              <p className="mt-6 text-lg leading-8 text-gray-400">
                Traditional validation is slow, expensive, and prone to human error. It&apos;s time for Validation 4.0.
              </p>
            </AnimatedSection>

            <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
              <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                <AnimatedSection delay={0.2} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <ClockIcon className="h-5 w-5 flex-none text-red-400" aria-hidden="true" />
                    Weeks of Delay
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Manual protocol writing bottlenecks project timelines. A single system can take 2-3 weeks to validate manually.
                    </p>
                  </dd>
                </AnimatedSection>

                <AnimatedSection delay={0.4} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <CurrencyDollarIcon className="h-5 w-5 flex-none text-red-400" aria-hidden="true" />
                    High Costs
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Validation consultants cost $150+/hr. We reduce generation costs to pennies per test suite.
                    </p>
                  </dd>
                </AnimatedSection>

                <AnimatedSection delay={0.6} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <ShieldCheckIcon className="h-5 w-5 flex-none text-red-400" aria-hidden="true" />
                    Compliance Risks
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Manual scripts often miss requirements or lack traceability, leading to painful audit findings.
                    </p>
                  </dd>
                </AnimatedSection>
              </dl>
            </div>
          </div>
        </div>

        {/* Solution Section */}
        <div className="py-16 sm:py-24 relative overflow-hidden">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_bottom,theme(colors.blue.900),transparent)] opacity-20" />
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <AnimatedSection className="mx-auto max-w-2xl lg:text-center">
              <h2 className="text-base font-semibold leading-7 text-blue-400">Validation 4.0</h2>
              <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                AI-Driven Computer Software Assurance (CSA)
              </p>
              <p className="mt-6 text-lg leading-8 text-gray-400">
                Shift from documentation-heavy validation to critical thinking and automated assurance.
              </p>
            </AnimatedSection>

            <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
              <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
                <AnimatedSection delay={0.2} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <CheckCircleIcon className="h-5 w-5 flex-none text-green-400" aria-hidden="true" />
                    95% Faster
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Generate complete, compliant OQ test suites in 8-12 minutes.
                    </p>
                  </dd>
                </AnimatedSection>

                <AnimatedSection delay={0.4} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <CheckCircleIcon className="h-5 w-5 flex-none text-green-400" aria-hidden="true" />
                    Audit Ready
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Full ALCOA+ data integrity, electronic signatures (21 CFR Part 11), and immutable audit trails.
                    </p>
                  </dd>
                </AnimatedSection>

                <AnimatedSection delay={0.6} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                    <CheckCircleIcon className="h-5 w-5 flex-none text-green-400" aria-hidden="true" />
                    Risk-Based
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-400">
                    <p className="flex-auto">
                      Automatic GAMP 5 categorization ensures you focus testing efforts where risk is highest.
                    </p>
                  </dd>
                </AnimatedSection>
              </dl>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <AnimatedSection className="relative isolate mt-32 px-6 py-32 sm:mt-56 sm:px-8">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(45rem_50rem_at_top,theme(colors.indigo.100),white)] opacity-20" />
          <div className="absolute inset-y-0 right-1/2 -z-10 mr-16 w-[200%] origin-bottom-left skew-x-[-30deg] bg-slate-900 shadow-xl shadow-indigo-600/10 ring-1 ring-indigo-50 sm:mr-28 lg:mr-0 xl:mr-16 xl:origin-center" />
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to modernize your validation?
              <br />
              Start generating tests today.
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-gray-300">
              Join the Validation 4.0 revolution. Secure, compliant, and efficient.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <a
                href="/generate"
                className="rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
              >
                Get Started
              </a>
            </div>
          </div>
        </AnimatedSection>
      </Layout>
    </>
  );
}
