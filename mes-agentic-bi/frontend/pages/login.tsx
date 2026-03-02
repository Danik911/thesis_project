import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

import { useAuth } from '@/lib/auth';

export default function LoginPage() {
  const { user, loading, error, signInUser, confirmNewPassword, authEnabled } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [challenge, setChallenge] = useState<string | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  // Redirect if already logged in or auth disabled
  useEffect(() => {
    if (!loading && (!authEnabled || user)) {
      router.replace('/agentic-bi');
    }
  }, [loading, authEnabled, user, router]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setLocalError(null);

    try {
      const result = await signInUser(email, password);
      if (result.challengeName === 'NEW_PASSWORD_REQUIRED') {
        setChallenge('NEW_PASSWORD_REQUIRED');
      } else {
        router.replace('/agentic-bi');
      }
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNewPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setLocalError(null);

    try {
      await confirmNewPassword(newPassword);
      router.replace('/agentic-bi');
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : 'Password change failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const displayError = localError || error;

  return (
    <>
      <Head>
        <title>Sign In - MES Agentic BI</title>
      </Head>

      <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <h1
            className="text-3xl font-bold text-cyan-300 text-center mb-2"
            style={{ fontFamily: 'var(--font-display)' }}
          >
            MES Agentic BI
          </h1>
          <p className="text-slate-400 text-sm text-center mb-8">
            Sign in to access your data
          </p>

          {challenge === 'NEW_PASSWORD_REQUIRED' ? (
            <form onSubmit={handleNewPassword} className="space-y-4">
              <p className="text-amber-300 text-sm text-center">
                You must set a new password before continuing.
              </p>

              <div>
                <label htmlFor="newPassword" className="block text-xs text-slate-400 mb-1">
                  New Password
                </label>
                <input
                  id="newPassword"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={12}
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25 transition-colors"
                  placeholder="Min. 12 characters"
                />
              </div>

              {displayError && (
                <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                  {displayError}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className={`w-full py-2.5 rounded-lg text-sm font-medium transition-all ${
                  submitting
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                }`}
              >
                {submitting ? 'Updating...' : 'Set New Password'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSignIn} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-xs text-slate-400 mb-1">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25 transition-colors"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-xs text-slate-400 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-2.5 rounded-lg bg-slate-900 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25 transition-colors"
                  placeholder="Your password"
                />
              </div>

              {displayError && (
                <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                  {displayError}
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className={`w-full py-2.5 rounded-lg text-sm font-medium transition-all ${
                  submitting
                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                    : 'bg-cyan-600 hover:bg-cyan-500 text-white'
                }`}
              >
                {submitting ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          )}
        </div>
      </div>
    </>
  );
}
