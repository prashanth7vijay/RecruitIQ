import { createContext, useContext, useEffect, useState, useCallback } from "react";
import {
  candidateApiClient,
  setCandidateAccessToken,
  setCandidateUnauthenticatedHandler,
} from "../lib/candidateApiClient";
import { decodeJwtPayload } from "../lib/jwt";

const CandidateAuthContext = createContext(null);

export function CandidateAuthProvider({ children }) {
  const [candidate, setCandidate] = useState(null);
  const [status, setStatus] = useState("anonymous"); // anonymous | authenticated

  const clearSession = useCallback(() => {
    setCandidateAccessToken(null);
    setCandidate(null);
    setStatus("anonymous");
  }, []);

  const applyToken = useCallback((accessToken) => {
    setCandidateAccessToken(accessToken);
    const claims = decodeJwtPayload(accessToken);
    setCandidate(claims ? { id: claims.sub } : null);
    setStatus("authenticated");
  }, []);

  useEffect(() => {
    setCandidateUnauthenticatedHandler(clearSession);
  }, [clearSession]);

  const login = useCallback(
    async ({ email, password }) => {
      const response = await candidateApiClient.post("/candidate-auth/login", { email, password });
      applyToken(response.data.data.access_token);
    },
    [applyToken]
  );

  const signup = useCallback(
    async ({ email, password, firstName, lastName, phone }) => {
      const response = await candidateApiClient.post("/candidate-auth/signup", {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
        phone: phone || undefined,
      });
      applyToken(response.data.data.access_token);
    },
    [applyToken]
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  return (
    <CandidateAuthContext.Provider value={{ candidate, status, login, signup, logout }}>
      {children}
    </CandidateAuthContext.Provider>
  );
}

export function useCandidateAuth() {
  const ctx = useContext(CandidateAuthContext);
  if (!ctx) throw new Error("useCandidateAuth must be used within CandidateAuthProvider");
  return ctx;
}
