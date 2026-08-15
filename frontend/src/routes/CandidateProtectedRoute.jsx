import { Navigate } from "react-router-dom";
import { useCandidateAuth } from "../stores/CandidateAuthContext";

export function CandidateProtectedRoute({ children }) {
  const { status } = useCandidateAuth();

  if (status === "anonymous") {
    return <Navigate to="/portal/login" replace />;
  }

  return children;
}
