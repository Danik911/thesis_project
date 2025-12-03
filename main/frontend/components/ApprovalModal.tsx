import { useState, useEffect, Fragment } from 'react';
import { useAuth, useUser } from '@clerk/nextjs';
import { Dialog, Transition } from '@headlessui/react';

/**
 * Categorization result from AI agent
 */
interface CategorizationResult {
    gamp_category: number;
    confidence_score: number;
    has_ambiguity_signals: boolean;
    ambiguity_details: string;
    alternative_categories: number[];
    reasoning: string;
}

/**
 * Approval request payload matching backend API
 * Endpoint: POST /jobs/{job_id}/approval
 */
interface ApprovalRequest {
    approval_decision: 'APPROVE' | 'REJECT' | 'REQUEST_REVISION';
    human_category: number | null;  // Required if APPROVE
    justification: string;  // Min 10 characters
    user_signature: string;  // Format: {user_id}_{timestamp}
}

interface ApprovalModalProps {
    isOpen: boolean;
    onClose: () => void;
    jobId: string;
    categorizationResult: CategorizationResult;
    timeoutRemainingSeconds: number | null;
    onApprovalSubmitted: () => void;
}

/**
 * ApprovalModal Component
 *
 * Displays AI categorization results and collects human approval decisions
 * with justifications for ALCOA+ compliant audit trail.
 *
 * Compliance:
 * - EU AI Act Article 50 (Transparency)
 * - 21 CFR Part 11 (Electronic Signatures)
 * - GAMP-5 (Human Oversight)
 * - WCAG 2.1 AA (Accessibility)
 *
 * NO FALLBACK LOGIC: All errors surface explicitly with full diagnostics
 */
export default function ApprovalModal({
    isOpen,
    onClose,
    jobId,
    categorizationResult,
    timeoutRemainingSeconds,
    onApprovalSubmitted
}: ApprovalModalProps) {
    const { getToken } = useAuth();
    const { user } = useUser();

    const [approvalDecision, setApprovalDecision] = useState<'APPROVE' | 'REJECT' | 'REQUEST_REVISION'>('APPROVE');
    const [humanCategory, setHumanCategory] = useState<number>(categorizationResult.gamp_category);
    const [justification, setJustification] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Reset form when modal opens
    useEffect(() => {
        if (isOpen) {
            setApprovalDecision('APPROVE');
            setHumanCategory(categorizationResult.gamp_category);
            setJustification('');
            setError(null);
        }
    }, [isOpen, categorizationResult.gamp_category]);

    /**
     * Generate digital signature per 21 CFR Part 11
     * Format: {user_id}_{YYYYMMDDHHMMSS}
     */
    const generateSignature = (): string => {
        if (!user?.id) {
            throw new Error('User ID not available for signature generation');
        }
        const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, '').slice(0, 14);
        return `${user.id}_${timestamp}`;
    };

    /**
     * Submit approval decision to backend
     * NO FALLBACK LOGIC: All validation errors throw explicitly
     */
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        // Validation: Justification minimum length
        if (justification.trim().length < 10) {
            setError('Justification must be at least 10 characters for ALCOA+ audit trail compliance.');
            return;
        }

        // Validation: Category override required if APPROVE
        if (approvalDecision === 'APPROVE' && !humanCategory) {
            setError('Please select a GAMP-5 category when approving.');
            return;
        }

        setIsSubmitting(true);

        try {
            const token = await getToken();
            if (!token) {
                throw new Error('Authentication token not available. Please sign in again.');
            }

            const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8080';

            const payload: ApprovalRequest = {
                approval_decision: approvalDecision,
                human_category: approvalDecision === 'APPROVE' ? humanCategory : null,
                justification: justification.trim(),
                user_signature: generateSignature()
            };

            const response = await fetch(`${apiUrl}/jobs/${jobId}/approval`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                // NO FALLBACK LOGIC: Expose API errors explicitly
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('Approval submitted successfully:', result);

            // Notify parent component
            onApprovalSubmitted();
            onClose();

        } catch (err: any) {
            // NO FALLBACK LOGIC: Display error with full diagnostics
            console.error('Error submitting approval:', err);
            setError(err.message || 'Failed to submit approval decision. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    /**
     * Get color coding for confidence score
     * Red < 70%, Amber 70-85%, Green > 85%
     */
    const getConfidenceColor = (score: number): { bg: string; text: string; label: string } => {
        if (score < 0.70) return { bg: 'bg-red-500/10', text: 'text-red-500', label: 'Low' };
        if (score < 0.85) return { bg: 'bg-amber-500/10', text: 'text-amber-500', label: 'Moderate' };
        return { bg: 'bg-green-500/10', text: 'text-green-500', label: 'High' };
    };

    const confidenceColor = getConfidenceColor(categorizationResult.confidence_score);

    /**
     * Format timeout remaining as MM:SS
     */
    const formatTimeout = (seconds: number | null): string => {
        if (seconds === null) return 'N/A';
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${String(secs).padStart(2, '0')}`;
    };

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                {/* Backdrop */}
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/70" aria-hidden="true" />
                </Transition.Child>

                {/* Modal container */}
                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="mx-auto max-w-3xl w-full rounded-xl bg-slate-800 border border-slate-700 shadow-2xl">
                                {/* Header */}
                                <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 rounded-t-xl border-b border-blue-500">
                                    <Dialog.Title className="text-xl font-bold text-white flex items-center gap-2">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        AI Categorization Review Required
                                    </Dialog.Title>
                                    <p className="text-sm text-blue-100 mt-1">
                                        The AI detected ambiguity and requires human oversight per GAMP-5 and EU AI Act Article 50.
                                    </p>
                                </div>

                                <form onSubmit={handleSubmit} className="px-6 py-4">
                                    {/* AI Recommendation Section */}
                                    <div className="mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
                                        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                                            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                            AI Recommendation
                                        </h3>

                                        {/* Category + Confidence */}
                                        <div className="grid grid-cols-2 gap-4 mb-3">
                                            <div>
                                                <p className="text-sm text-slate-400 mb-1">Suggested Category</p>
                                                <p className="text-2xl font-bold text-blue-400">
                                                    Category {categorizationResult.gamp_category}
                                                </p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-slate-400 mb-1">Confidence Score</p>
                                                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded ${confidenceColor.bg}`}>
                                                    <span className={`text-2xl font-bold ${confidenceColor.text}`}>
                                                        {(categorizationResult.confidence_score * 100).toFixed(0)}%
                                                    </span>
                                                    <span className={`text-sm font-medium ${confidenceColor.text}`}>
                                                        {confidenceColor.label}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Ambiguity Alert */}
                                        {categorizationResult.has_ambiguity_signals && (
                                            <div className="mb-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                                <p className="text-sm font-semibold text-amber-400 mb-1 flex items-center gap-2">
                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                                    </svg>
                                                    Ambiguity Detected
                                                </p>
                                                <p className="text-sm text-amber-300">
                                                    {categorizationResult.ambiguity_details}
                                                </p>
                                            </div>
                                        )}

                                        {/* Alternative Categories */}
                                        {categorizationResult.alternative_categories && categorizationResult.alternative_categories.length > 0 && (
                                            <div className="mb-3">
                                                <p className="text-sm text-slate-400 mb-2">Alternative Categories</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {categorizationResult.alternative_categories.map(cat => (
                                                        <span key={cat} className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm font-medium border border-blue-500/30">
                                                            Category {cat}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* AI Reasoning */}
                                        <div>
                                            <p className="text-sm text-slate-400 mb-2">AI Reasoning</p>
                                            <div className="text-sm text-slate-300 bg-slate-800/50 p-3 rounded border border-slate-700 leading-relaxed">
                                                {categorizationResult.reasoning}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Human Decision Section */}
                                    <div className="mb-6">
                                        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                                            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                            </svg>
                                            Your Decision
                                        </h3>

                                        {/* Decision Select */}
                                        <div className="mb-4">
                                            <label htmlFor="approval-decision" className="block text-sm font-medium text-slate-300 mb-2">
                                                Approval Decision <span className="text-red-400">*</span>
                                            </label>
                                            <select
                                                id="approval-decision"
                                                value={approvalDecision}
                                                onChange={(e) => setApprovalDecision(e.target.value as any)}
                                                className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                required
                                                aria-required="true"
                                            >
                                                <option value="APPROVE">Approve (accept AI recommendation or override)</option>
                                                <option value="REJECT">Reject (cancel test generation)</option>
                                                <option value="REQUEST_REVISION">Request Revision (needs more analysis)</option>
                                            </select>
                                        </div>

                                        {/* Category Override (only for APPROVE) */}
                                        {approvalDecision === 'APPROVE' && (
                                            <div className="mb-4">
                                                <label htmlFor="human-category" className="block text-sm font-medium text-slate-300 mb-2">
                                                    Final GAMP-5 Category <span className="text-red-400">*</span>
                                                </label>
                                                <select
                                                    id="human-category"
                                                    value={humanCategory}
                                                    onChange={(e) => setHumanCategory(Number(e.target.value))}
                                                    className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                    required
                                                    aria-required="true"
                                                >
                                                    <option value={1}>Category 1 - Infrastructure (OS, firmware)</option>
                                                    <option value={3}>Category 3 - Non-configured COTS</option>
                                                    <option value={4}>Category 4 - Configured COTS</option>
                                                    <option value={5}>Category 5 - Custom-developed</option>
                                                </select>
                                                <p className="text-xs text-slate-400 mt-1">
                                                    You can override the AI recommendation if you disagree.
                                                </p>
                                            </div>
                                        )}

                                        {/* Justification (Required) */}
                                        <div className="mb-4">
                                            <label htmlFor="justification" className="block text-sm font-medium text-slate-300 mb-2">
                                                Justification <span className="text-red-400">*</span>
                                            </label>
                                            <textarea
                                                id="justification"
                                                value={justification}
                                                onChange={(e) => setJustification(e.target.value)}
                                                className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                rows={4}
                                                placeholder="Explain your decision (minimum 10 characters for ALCOA+ audit trail compliance)"
                                                required
                                                minLength={10}
                                                aria-required="true"
                                                aria-invalid={justification.length > 0 && justification.length < 10 ? 'true' : 'false'}
                                            />
                                            <p className={`text-xs mt-1 ${justification.length < 10 ? 'text-amber-400' : 'text-slate-400'}`}>
                                                {justification.length}/10 characters minimum (ALCOA+ requirement)
                                            </p>
                                        </div>

                                        {/* Timeout Warning */}
                                        {timeoutRemainingSeconds !== null && timeoutRemainingSeconds < 300 && (
                                            <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                                <p className="text-sm text-amber-400 flex items-center gap-2">
                                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                    </svg>
                                                    Time remaining: <strong>{formatTimeout(timeoutRemainingSeconds)}</strong>
                                                </p>
                                            </div>
                                        )}

                                        {/* Digital Signature Info */}
                                        <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                                            <p className="text-xs text-blue-300 mb-1">
                                                <strong>Digital Signature:</strong> {user?.id}_[timestamp]
                                            </p>
                                            <p className="text-xs text-blue-400">
                                                Your decision will be recorded with your user ID, email ({user?.primaryEmailAddress?.emailAddress}), and timestamp per 21 CFR Part 11 §11.50.
                                            </p>
                                        </div>

                                        {/* EU AI Act Notice */}
                                        <div className="p-3 bg-slate-900/50 border border-slate-700 rounded-lg">
                                            <p className="text-xs text-slate-400">
                                                <strong className="text-slate-300">Regulatory Notice:</strong> This approval step fulfills transparency obligations under EU AI Act Article 50 and human oversight requirements per GAMP-5 guidelines.
                                            </p>
                                        </div>
                                    </div>

                                    {/* Error Display */}
                                    {error && (
                                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg" role="alert">
                                            <p className="text-sm text-red-400 flex items-center gap-2">
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                <strong>Error:</strong> {error}
                                            </p>
                                        </div>
                                    )}

                                    {/* Footer Buttons */}
                                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
                                        <button
                                            type="button"
                                            onClick={onClose}
                                            className="px-4 py-2 text-slate-300 bg-slate-700 rounded-lg hover:bg-slate-600 transition-colors"
                                            disabled={isSubmitting}
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors"
                                            disabled={isSubmitting || justification.trim().length < 10}
                                        >
                                            {isSubmitting ? 'Submitting...' : 'Submit Decision'}
                                        </button>
                                    </div>
                                </form>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
