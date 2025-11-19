/**
 * Hook for managing user session
 */

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api";
import type { SessionInfo, LoginRequest } from "@/lib/types";

export function useSession() {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkSession = useCallback(async () => {
    try {
      const sessionInfo = await apiClient.getSession();
      setSession(sessionInfo);
      setError(null);
      return sessionInfo;
    } catch (err) {
      setSession(null);
      setError(err instanceof Error ? err.message : "Failed to get session");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.login(credentials);
      await checkSession();
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Login failed";
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [checkSession]);

  const logout = useCallback(async () => {
    try {
      await apiClient.logout();
      setSession(null);
    } catch (err) {
      console.error("Logout error:", err);
    }
  }, []);

  useEffect(() => {
    checkSession();
  }, [checkSession]);

  // Auto-refresh session every minute
  useEffect(() => {
    if (!session) return;

    const interval = setInterval(() => {
      checkSession();
    }, 60000); // Every minute

    return () => clearInterval(interval);
  }, [session, checkSession]);

  return {
    session,
    loading,
    error,
    login,
    logout,
    checkSession,
    isAuthenticated: !!session && session.is_valid,
  };
}

