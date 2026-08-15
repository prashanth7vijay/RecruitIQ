import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { apiClient, setAccessToken, setUnauthenticatedHandler } from "../lib/apiClient";
import { decodeJwtPayload } from "../lib/jwt";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [permissions, setPermissions] = useState([]);
  const [status, setStatus] = useState("checking"); // checking | authenticated | anonymous

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    setPermissions([]);
    setStatus("anonymous");
  }, []);

  const applyToken = useCallback(async (accessToken) => {
    setAccessToken(accessToken);
    const claims = decodeJwtPayload(accessToken);
    setUser(
      claims
        ? {
            id: claims.sub,
            tenantId: claims.tenant_id,
            roleId: claims.role_id,
            mustChangePassword: Boolean(claims.must_change_password),
          }
        : null
    );

    try {
      const permsRes = await apiClient.get("/auth/permissions");
      setPermissions(permsRes.data.data.permissions);
    } catch {
      setPermissions([]);
    }
  }, []);

  useEffect(() => {
    setUnauthenticatedHandler(clearSession);
  }, [clearSession]);

  useEffect(() => {
    apiClient
      .post("/auth/refresh")
      .then(async (res) => {
        await applyToken(res.data.data.access_token);
        setStatus("authenticated");
      })
      .catch(() => {
        setStatus("anonymous");
      });
  }, [applyToken]);

  const login = useCallback(async ({ companySlug, email, password, rememberMe }) => {
    const response = await apiClient.post("/auth/login", {
      company_slug: companySlug,
      email,
      password,
      remember_me: rememberMe,
    });
    await applyToken(response.data.data.access_token);
    setStatus("authenticated");
  }, [applyToken]);

  const signup = useCallback(async ({ companyName, companySlug, email, password, firstName, lastName }) => {
    await apiClient.post("/auth/signup", {
      company_name: companyName,
      company_slug: companySlug,
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    });
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const changePassword = useCallback(
    async ({ currentPassword, newPassword }) => {
      const response = await apiClient.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      await applyToken(response.data.data.access_token);
    },
    [applyToken]
  );

  const hasPermission = useCallback(
    (code) => permissions.includes(code),
    [permissions]
  );

  return (
    <AuthContext.Provider value={{ user, permissions, hasPermission, status, login, signup, logout, changePassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
