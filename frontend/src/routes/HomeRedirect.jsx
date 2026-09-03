import { Navigate } from "react-router-dom";
import { useAuth } from "../stores/AuthContext";

const LANDING_PRIORITY = [
  { path: "/candidates", anyOf: ["candidate.view_all"] },
  { path: "/refer", anyOf: ["referral.submit"] },
  { path: "/my-interviews", anyOf: [] },
];

export function HomeRedirect() {
  const { hasPermission } = useAuth();
  const target = LANDING_PRIORITY.find(
    (route) => route.anyOf.length === 0 || route.anyOf.some((code) => hasPermission(code))
  );
  return <Navigate to={target.path} replace />;
}