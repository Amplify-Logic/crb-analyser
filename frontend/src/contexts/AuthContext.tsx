/**
 * Authentication Context
 * Manages user authentication state, login, signup, and logout
 * Uses Supabase Auth via backend API with HTTP-only cookies
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { logger } from '../utils/logger'
import apiClient from '../services/apiClient'

interface User {
  id: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  workspace_id: string;
  role: string;
  subscription_status?: string;
  plan_type?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName?: string) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // Fetch current user profile using HTTP-only cookies
  const fetchUser = useCallback(async () => {
    try {
      const { data: userData } = await apiClient.get<User>('/api/auth/me', {
        timeout: 10000,
      });
      setUser(userData);
      // Store workspace_id in sessionStorage for other services
      if (userData.workspace_id) {
        sessionStorage.setItem('crb_workspace_id', userData.workspace_id);
      }
    } catch (error: any) {
      if (error?.status === 401) {
        setUser(null);
        sessionStorage.removeItem('crb_workspace_id');
      } else {
        logger.error('Failed to fetch user:', error);
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Check auth on mount
  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Login
  const login = useCallback(async (email: string, password: string) => {
    try {
      await apiClient.post('/api/auth/login', { email, password }, {
        timeout: 15000,
      });

      // Fetch full user profile
      await fetchUser();

      // Navigate to dashboard or intended destination
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (error: any) {
      logger.error('Login error:', error);
      throw new Error(error?.detail || error?.message || 'Login failed');
    }
  }, [navigate, fetchUser, location.state]);

  // Signup
  const signup = useCallback(async (email: string, password: string, fullName?: string) => {
    try {
      const { data } = await apiClient.post<{ user: User }>('/api/auth/signup', {
        email, password, full_name: fullName,
      }, {
        timeout: 15000,
      });

      // Fetch full user profile
      await fetchUser();

      // Navigate to dashboard
      navigate('/dashboard');

      return data.user;
    } catch (error: any) {
      logger.error('Signup error:', error);
      throw new Error(error?.detail || error?.message || 'Signup failed');
    }
  }, [navigate, fetchUser]);

  // Logout
  const logout = useCallback(async () => {
    try {
      await apiClient.post('/api/auth/logout', undefined, {
        timeout: 10000,
      });
    } catch (error) {
      logger.error('Logout error:', error);
    } finally {
      setUser(null);
      sessionStorage.removeItem('crb_workspace_id');
      navigate('/login');
    }
  }, [navigate]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  // Memoize context value
  const value: AuthContextType = useMemo(() => ({
    user,
    loading,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    refreshUser,
  }), [user, loading, login, signup, logout, refreshUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Protected Route component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/login', { state: { from: location }, replace: true });
    }
  }, [isAuthenticated, loading, navigate, location]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : null;
};

// Anonymous Route component - redirects logged-in users to dashboard
interface AnonymousRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export const AnonymousRoute: React.FC<AnonymousRouteProps> = ({
  children,
  redirectTo = '/dashboard'
}) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, loading, navigate, redirectTo]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return !isAuthenticated ? <>{children}</> : null;
};

export default AuthContext;
