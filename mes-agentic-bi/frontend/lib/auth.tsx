'use client';

import { Amplify } from 'aws-amplify';
import {
  confirmSignIn,
  fetchAuthSession,
  getCurrentUser,
  signIn,
  signOut,
} from 'aws-amplify/auth';
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';

// Configure Amplify from env vars
const userPoolId = process.env.NEXT_PUBLIC_BI_COGNITO_USER_POOL_ID || '';
const userPoolClientId = process.env.NEXT_PUBLIC_BI_COGNITO_CLIENT_ID || '';

if (userPoolId && userPoolClientId) {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId,
      },
    },
  });
}

export interface AuthUser {
  sub: string;
  email: string;
  role: 'Admin' | 'Operator';
  site: string | null;
  groups: string[];
  username: string;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  signInUser: (username: string, password: string) => Promise<{ challengeName?: string }>;
  confirmNewPassword: (newPassword: string) => Promise<void>;
  signOutUser: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  isAdmin: boolean;
  authEnabled: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const authEnabled = process.env.NEXT_PUBLIC_BI_AUTH_ENABLED === 'true';

  useEffect(() => {
    if (!authEnabled) {
      setLoading(false);
      return;
    }
    checkCurrentUser();
  }, [authEnabled]);

  const extractUserFromSession = async (): Promise<AuthUser | null> => {
    try {
      const session = await fetchAuthSession();
      if (!session.tokens?.idToken) return null;

      const payload = session.tokens.idToken.payload;
      const groups = (payload['cognito:groups'] as string[]) || [];

      return {
        sub: payload.sub as string,
        email: (payload.email as string) || '',
        role: groups.includes('Admin') ? 'Admin' : 'Operator',
        site: (payload['custom:site'] as string) || null,
        groups,
        username: (payload['cognito:username'] as string) || '',
      };
    } catch {
      return null;
    }
  };

  const checkCurrentUser = async () => {
    try {
      await getCurrentUser();
      const extracted = await extractUserFromSession();
      setUser(extracted);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const signInUser = async (
    username: string,
    password: string
  ): Promise<{ challengeName?: string }> => {
    setError(null);
    try {
      const result = await signIn({ username, password });

      if (
        result.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED'
      ) {
        return { challengeName: 'NEW_PASSWORD_REQUIRED' };
      }

      if (result.isSignedIn) {
        const extracted = await extractUserFromSession();
        setUser(extracted);
      }
      return {};
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Sign in failed';
      setError(message);
      throw err;
    }
  };

  const confirmNewPassword = async (newPassword: string) => {
    setError(null);
    try {
      const result = await confirmSignIn({ challengeResponse: newPassword });
      if (result.isSignedIn) {
        const extracted = await extractUserFromSession();
        setUser(extracted);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Password change failed';
      setError(message);
      throw err;
    }
  };

  const signOutUser = async () => {
    await signOut();
    setUser(null);
  };

  const getAccessToken = async (): Promise<string | null> => {
    if (!authEnabled) return null;
    try {
      const session = await fetchAuthSession();
      return session.tokens?.idToken?.toString() || null;
    } catch {
      return null;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        signInUser,
        confirmNewPassword,
        signOutUser,
        getAccessToken,
        isAdmin: user?.role === 'Admin',
        authEnabled,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
