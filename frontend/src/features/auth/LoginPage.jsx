import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../stores/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", companySlug: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(form);
      navigate("/candidates");
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-ink-900 p-12 text-ink-50 lg:flex">
        <div className="font-display text-xl tracking-tight">RecruitIQ</div>
        <div>
          <p className="font-display text-4xl leading-tight text-ink-50">
            Every candidate you've
            <br />
            ever met, still findable.
          </p>
          <p className="mt-4 max-w-sm text-sm text-ink-300">
            Hiring pipelines, interview intelligence, and a talent pool
            that never starts from zero.
          </p>
        </div>
        <p className="text-xs text-ink-400">Recruitment intelligence, not guesswork.</p>
      </div>

      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h1 className="font-display text-2xl text-ink-900">Sign in</h1>
          <p className="mt-1 text-sm text-ink-500">Welcome back — pick up where you left off.</p>

          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
            <Input
              id="companySlug"
              label="Organization"
              placeholder="your-company"
              value={form.companySlug}
              onChange={(e) => setForm({ ...form, companySlug: e.target.value })}
              required
            />
            <Input
              id="email"
              label="Email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
            <Input
              id="password"
              label="Password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
            {error && (
              <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
            )}
            <Button type="submit" disabled={submitting} className="mt-2 w-full">
              {submitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-ink-500">
            New to RecruitIQ?{" "}
            <Link to="/signup" className="font-medium text-signal-600 hover:text-signal-700">
              Create an organization
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
