import { useAuth } from "../stores/AuthContext";
import { NotAuthorizedPage } from "./NotAuthorizedPage";

export function RequirePermission({ anyOf, children }) {
  const { hasPermission } = useAuth();
  const allowed = anyOf.some((code) => hasPermission(code));
 
  if (!allowed) {
    return <NotAuthorizedPage />;
  }
 
  return children;
}