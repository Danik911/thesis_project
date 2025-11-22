import React, { Fragment, useState, useEffect } from 'react';
import { Dialog, Transition, Tab } from '@headlessui/react';
import { XMarkIcon, ServerIcon, ClipboardDocumentCheckIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import { allFrameworks } from '@/utils/complianceContent';
import { motion, AnimatePresence } from 'framer-motion';

interface HowItWorksModalProps {
    isOpen: boolean;
    onClose: () => void;
}

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ');
}

export default function HowItWorksModal({ isOpen, onClose }: HowItWorksModalProps) {
    const [selectedIndex, setSelectedIndex] = useState(0);

    const tabs = [
        { name: 'Architecture', icon: ServerIcon },
        { name: 'Workflow', icon: ClipboardDocumentCheckIcon },
        { name: 'Compliance', icon: ShieldCheckIcon },
    ];

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto overflow-x-hidden p-4 sm:p-0">
            <div className="fixed inset-0 bg-gray-900/80 backdrop-blur-sm transition-opacity" onClick={onClose} />

            <div className="relative transform overflow-hidden rounded-xl bg-slate-900 text-left shadow-2xl transition-all sm:my-8 sm:w-full sm:max-w-5xl border border-slate-700 z-10">
                <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
                    <button
                        type="button"
                        className="rounded-md bg-slate-900 text-gray-400 hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                        onClick={onClose}
                    >
                        <span className="sr-only">Close</span>
                        <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                    </button>
                </div>

                <div className="flex h-[85vh] flex-col">
                    {/* Header */}
                    <div className="px-6 py-6 border-b border-slate-700 bg-slate-800/50">
                        <h3 className="text-2xl font-bold leading-6 text-white">
                            How It Works
                        </h3>
                        <p className="mt-2 text-sm text-gray-400">
                            Understand the AI-driven validation process, system architecture, and compliance standards.
                        </p>
                    </div>

                    {/* Tabs */}
                    <div className="relative flex-1 w-full overflow-hidden">
                        <Tab.Group selectedIndex={selectedIndex} onChange={setSelectedIndex}>
                            <div className="absolute inset-y-0 left-0 w-64 bg-slate-800/30 border-r border-slate-700 overflow-y-auto">
                                <Tab.List className="flex flex-col space-y-1 p-4">
                                    {tabs.map((tab) => (
                                        <Tab
                                            key={tab.name}
                                            className={({ selected }) =>
                                                classNames(
                                                    selected
                                                        ? 'bg-slate-800 text-blue-400 shadow-sm ring-1 ring-slate-700'
                                                        : 'text-gray-400 hover:bg-slate-800/50 hover:text-white',
                                                    'group flex items-center rounded-md px-3 py-2 text-sm font-medium outline-none transition-all duration-200'
                                                )
                                            }
                                        >
                                            <tab.icon
                                                className={classNames(
                                                    selectedIndex === tabs.indexOf(tab) ? 'text-blue-400' : 'text-gray-500 group-hover:text-gray-400',
                                                    'mr-3 h-5 w-5 flex-shrink-0'
                                                )}
                                                aria-hidden="true"
                                            />
                                            {tab.name}
                                        </Tab>
                                    ))}
                                </Tab.List>
                            </div>

                            <Tab.Panels className="absolute inset-y-0 left-64 right-0 overflow-y-auto p-8 bg-slate-900">
                                <AnimatePresence mode="wait">
                                    {/* Architecture Tab */}
                                    <Tab.Panel
                                        as={motion.div}
                                        key="architecture"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{ duration: 0.2 }}
                                        className="space-y-8 focus:outline-none"
                                    >
                                        <div>
                                            <h3 className="text-xl font-semibold text-white mb-4">System Architecture</h3>
                                            <p className="text-gray-400 mb-6">
                                                A robust, containerized microservices architecture designed for scalability, security, and compliance.
                                            </p>

                                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                                                    <h4 className="font-medium text-white mb-3 flex items-center">
                                                        <span className="bg-blue-900/30 text-blue-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded border border-blue-800">Current</span>
                                                        Local Development (Docker Compose)
                                                    </h4>
                                                    <ul className="space-y-3 text-sm text-gray-400">
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>PostgreSQL 15 + pgvector:</strong> Metadata & vector storage</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>LocalStack:</strong> AWS SQS emulation for job queues</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>FastAPI Backend:</strong> REST API & business logic</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>Python Worker:</strong> Async workflow execution</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>Next.js Frontend:</strong> Interactive dashboard</span>
                                                        </li>
                                                    </ul>
                                                </div>

                                                <div className="bg-indigo-900/10 rounded-lg p-6 border border-indigo-500/20">
                                                    <h4 className="font-medium text-white mb-3 flex items-center">
                                                        <span className="bg-indigo-900/30 text-indigo-300 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded border border-indigo-800">Planned</span>
                                                        AWS Production
                                                    </h4>
                                                    <ul className="space-y-3 text-sm text-gray-400">
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>ECS Fargate:</strong> Serverless container orchestration</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>Aurora Serverless v2:</strong> Scalable PostgreSQL</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>Amazon Bedrock:</strong> Secure LLM access</span>
                                                        </li>
                                                        <li className="flex items-start">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 mt-1.5 mr-2 flex-shrink-0"></span>
                                                            <span><strong>S3 + Object Lock:</strong> WORM storage for audit trails</span>
                                                        </li>
                                                    </ul>
                                                </div>
                                            </div>

                                            <div className="mt-8">
                                                <h4 className="font-medium text-white mb-4">Key Technologies</h4>
                                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                                    <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg text-center">
                                                        <div className="text-blue-400 font-bold text-lg mb-1">DeepSeek V3.1</div>
                                                        <div className="text-xs text-gray-500">671B MoE LLM</div>
                                                    </div>
                                                    <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg text-center">
                                                        <div className="text-blue-400 font-bold text-lg mb-1">LangFuse</div>
                                                        <div className="text-xs text-gray-500">Observability</div>
                                                    </div>
                                                    <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg text-center">
                                                        <div className="text-blue-400 font-bold text-lg mb-1">ChromaDB</div>
                                                        <div className="text-xs text-gray-500">Vector Search</div>
                                                    </div>
                                                    <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg text-center">
                                                        <div className="text-blue-400 font-bold text-lg mb-1">Clerk</div>
                                                        <div className="text-xs text-gray-500">Authentication</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </Tab.Panel>

                                    {/* Workflow Tab */}
                                    <Tab.Panel
                                        as={motion.div}
                                        key="workflow"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{ duration: 0.2 }}
                                        className="focus:outline-none"
                                    >
                                        <h3 className="text-xl font-semibold text-white mb-4">10-Step Validation Workflow</h3>
                                        <p className="text-gray-400 mb-8">
                                            Our AI agents follow a strict, auditable process to ensure every test suite is GAMP driven.
                                        </p>

                                        <div className="relative border-l-2 border-slate-700 ml-3 space-y-8">
                                            {[
                                                { title: '1. Document Upload & Scan', desc: 'URS document is scanned for security threats (OWASP LLM Top 10) and sanitized.', time: '~30s' },
                                                { title: '2. GAMP-5 Categorization', desc: 'AI categorizes software (Category 1-5) with confidence scoring. No fallbacks allowed.', time: '~45s' },
                                                { title: '3. Risk Assessment', desc: 'Test count and rigor determined based on ICH Q9 quality risk management principles.', time: '~30s' },
                                                { title: '4. Parallel Agent Analysis', desc: 'Three independent agents (Context, Research, SME) analyze requirements concurrently to reduce bias.', time: '~2m' },
                                                { title: '5. RAG Data Gathering', desc: 'Relevant regulations retrieved from 26 indexed documents (21 CFR Part 11, EU Annex 11).', time: '~1m' },
                                                { title: '6. Human Oversight', desc: 'Low confidence (<80%) triggers mandatory human review per EU AI Act Article 14.', time: 'Variable' },
                                                { title: '7. Electronic Signature', desc: 'Cryptographic signature captures approval per 21 CFR Part 11 §11.50.', time: '~5s' },
                                                { title: '8. Test Generation', desc: 'DeepSeek V3 generates complete OQ test suite with steps and acceptance criteria.', time: '~3-5m' },
                                                { title: '9. ALCOA+ Validation', desc: 'Automated check against all 9 data integrity principles (Attributable, Legible, etc.).', time: '~15s' },
                                                { title: '10. Audit Trail Compilation', desc: 'Final compilation of immutable audit logs and trace IDs for full traceability.', time: '~10s' },
                                            ].map((step, idx) => (
                                                <motion.div
                                                    key={idx}
                                                    initial={{ opacity: 0, x: -20 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: idx * 0.1 }}
                                                    className="relative pl-8"
                                                >
                                                    <span className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-blue-600 ring-4 ring-slate-900" />
                                                    <div className="flex justify-between items-start">
                                                        <div>
                                                            <h4 className="font-semibold text-white">{step.title}</h4>
                                                            <p className="text-sm text-gray-400 mt-1">{step.desc}</p>
                                                        </div>
                                                        <span className="text-xs font-medium text-blue-400 bg-blue-900/20 px-2 py-1 rounded whitespace-nowrap ml-4 border border-blue-800">
                                                            {step.time}
                                                        </span>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </Tab.Panel>

                                    {/* Compliance Tab */}
                                    <Tab.Panel
                                        as={motion.div}
                                        key="compliance"
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        transition={{ duration: 0.2 }}
                                        className="focus:outline-none"
                                    >
                                        <h3 className="text-xl font-semibold text-white mb-4">Regulatory Compliance</h3>
                                        <p className="text-gray-400 mb-6">
                                            Built from the ground up to meet the most stringent pharmaceutical standards.
                                        </p>

                                        <div className="space-y-6">
                                            {allFrameworks.map((framework, idx) => (
                                                <motion.div
                                                    key={framework.id}
                                                    initial={{ opacity: 0, y: 20 }}
                                                    animate={{ opacity: 1, y: 0 }}
                                                    transition={{ delay: idx * 0.1 }}
                                                    className="bg-slate-800/50 border border-slate-700 rounded-lg p-5 hover:shadow-md transition-shadow"
                                                >
                                                    <div className="flex items-start">
                                                        <div className="flex-shrink-0 text-2xl mr-4">{framework.icon}</div>
                                                        <div className="flex-1">
                                                            <h4 className="text-lg font-medium text-white">{framework.fullName}</h4>
                                                            <p className="text-sm text-gray-400 mt-1">{framework.description}</p>

                                                            <div className="mt-4">
                                                                <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                                                                    <span>Implementation Status</span>
                                                                    <span className="font-medium text-green-400">
                                                                        {Math.round((framework.cards.filter(c => c.status === 'implemented').length / framework.cards.length) * 100)}% Coverage
                                                                    </span>
                                                                </div>
                                                                <div className="w-full bg-slate-700 rounded-full h-1.5">
                                                                    <div
                                                                        className="bg-green-500 h-1.5 rounded-full"
                                                                        style={{ width: `${(framework.cards.filter(c => c.status === 'implemented').length / framework.cards.length) * 100}%` }}
                                                                    ></div>
                                                                </div>
                                                            </div>

                                                            <div className="mt-4 flex flex-wrap gap-2">
                                                                {framework.cards.slice(0, 3).map(card => (
                                                                    <span key={card.id} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-gray-300">
                                                                        {card.title}
                                                                    </span>
                                                                ))}
                                                                {framework.cards.length > 3 && (
                                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-gray-500 border border-slate-700">
                                                                        +{framework.cards.length - 3} more
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </Tab.Panel>
                                </AnimatePresence>
                            </Tab.Panels>
                        </Tab.Group>
                    </div>

                    {/* Footer */}
                    <div className="bg-slate-800/50 px-6 py-4 flex justify-end border-t border-slate-700">
                        <button
                            type="button"
                            className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                            onClick={onClose}
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
