import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCandidateAuth } from "../../stores/CandidateAuthContext";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

export function CandidateSignupPage() {
  const { signup } = useCandidateAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", firstName: "", lastName: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signup(form);
      navigate("/portal", { replace: true });
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create your account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-4">
      <Card className="w-full max-w-sm p-8">
        <h1 className="font-display text-xl text-[var(--text-primary)]">Create your account</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)]">
          Use the same email you applied with to see your existing applications here too.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              id="signup-first-name"
              label="First name"
              value={form.firstName}
              onChange={(e) => setForm({ ...form, firstName: e.target.value })}
              required
            />
            <Input
              id="signup-last-name"
              label="Last name"
              value={form.lastName}
              onChange={(e) => setForm({ ...form, lastName: e.target.value })}
              required
            />
          </div>
          <Input
            id="signup-email"
            type="email"
            label="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <Input
            id="signup-password"
            type="password"
            label="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
            minLength={10}
          />
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Creating account…" : "Create account"}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-[var(--text-muted)]">
          Already have an account?{" "}
          <Link to="/portal/login" className="font-medium text-signal-600">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
