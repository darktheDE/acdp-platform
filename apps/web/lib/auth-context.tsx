"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch, type TokenResponse, type UserProfileDTO } from "@/lib/api-client";

interface AuthContextValue {
  user: UserProfileDTO | null;
  accessToken: string | null;
  loading: boolean;
  setSession: (token: TokenResponse) => void;
  logout: () => Promise<void>;
  refreshSession: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfileDTO | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshSession = useCallback(async (): Promise<string | null> => {
    try {
      const data = await apiFetch<TokenResponse>("/api/v1/auth/refresh", { method: "POST" });
      setAccessToken(data.access_token);
      setUser(data.user);
      return data.access_token;
    } catch {
      setAccessToken(null);
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    let active = true;
    (async () => {
      await refreshSession();
      if (active) setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [refreshSession]);

  const setSession = useCallback((token: TokenResponse) => {
    setAccessToken(token.access_token);
    setUser(token.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      if (accessToken) {
        await apiFetch<void>("/api/v1/auth/logout", {
          method: "POST",
          token: accessToken,
        });
      }
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, [accessToken]);

  return (
    <AuthContext.Provider value={{ user, accessToken, loading, setSession, logout, refreshSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
