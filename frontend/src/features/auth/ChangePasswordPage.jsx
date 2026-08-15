import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../stores/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";

export function ChangePasswordPage() {
  const { changePassword, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (newPassword.length < 10) {
      setError("New password must be at least 10 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation don't match.");
      return;
    }

    setSubmitting(true);
    try {
      await changePassword({ currentPassword, newPassword });
      navigate("/candidates", { replace: true });
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not change password. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-4">
      <Card className="w-full max-w-md p-8">
        <h1 className="font-display text-xl text-[var(--text-primary)]">Set a new password</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          You're signing in with a temporary password. Choose a permanent one to continue —
          you won't be able to access anything else until you do.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <Input
            id="current-password"
            type="password"
            label="Temporary password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <Input
            id="new-password"
            type="password"
            label="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={10}
          />
          <Input
            id="confirm-password"
            type="password"
            label="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
            minLength={10}
          />
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Setting password…" : "Set password and continue"}
          </Button>
        </form>

        <button
          type="button"
          onClick={logout}
          className="mt-4 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
        >
          Not you? Sign out
        </button>
      </Card>
    </div>
  );
}
