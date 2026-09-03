import { Link } from "react-router-dom";

export function NotAuthorizedPage(){
    return(
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <p className="font-display text-2xl text-[var(--text-primary)]">You don't have access to this page</p>
      <p className="mt-2 max-w-sm text-sm text-[var(--text-secondary)]">
        This area is restricted to people with the right permissions. If you think this is a
        mistake, ask an admin to check your role.
      </p>
      <Link to="/" className="mt-6 text-sm font-medium text-signal-600 hover:text-signal-700">
        ← Back to your workspace
      </Link>
    </div>
    );
}