import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCandidateAuth } from "../../stores/CandidateAuthContext";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

export function CandidateLoginPage() {
  const { login } = useCandidateAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({ email, password });
      navigate("/portal", { replace: true });
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-4">
      <Card className="w-full max-w-sm p-8">
        <h1 className="font-display text-xl text-[var(--text-primary)]">Track your application</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Sign in to see your application status, interviews, and offers.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <Input
            id="candidate-email"
            type="email"
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            id="candidate-password"
            type="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-[var(--text-muted)]">
          Applied before but never set a password?{" "}
          <Link to="/portal/signup" className="font-medium text-signal-600">
            Create an account
          </Link>{" "}
          with the same email to see your existing applications.
        </p>
      </Card>
    </div>
  );
}
