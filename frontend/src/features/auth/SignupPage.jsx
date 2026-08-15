import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../stores/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

function slugify(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    companyName: "",
    companySlug: "",
    email: "",
    password: "",
    firstName: "",
    lastName: "",
  });
  const [slugEdited, setSlugEdited] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  function handleCompanyNameChange(value) {
    setForm((prev) => ({
      ...prev,
      companyName: value,
      companySlug: slugEdited ? prev.companySlug : slugify(value),
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signup(form);
      setDone(true);
    } catch (err) {
      const details = err.response?.data?.error?.details;
      setError(
        details?.[0]?.message ??
          err.response?.data?.error?.message ??
          "Something went wrong. Try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink-50 px-8">
        <div className="max-w-sm text-center">
          <p className="font-display text-2xl text-ink-900">Organization created</p>
          <p className="mt-2 text-sm text-ink-500">
            Sign in with <span className="font-medium text-ink-700">{form.companySlug}</span> to
            get started.
          </p>
          <Button onClick={() => navigate("/login")} className="mt-6">
            Go to sign in
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 px-8">
      <div className="w-full max-w-sm">
        <h1 className="font-display text-2xl text-ink-900">Create your organization</h1>
        <p className="mt-1 text-sm text-ink-500">
          You'll be the first admin — invite your team once you're in.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
          <Input
            id="companyName"
            label="Company name"
            value={form.companyName}
            onChange={(e) => handleCompanyNameChange(e.target.value)}
            required
          />
          <Input
            id="companySlug"
            label="Organization URL"
            value={form.companySlug}
            onChange={(e) => {
              setSlugEdited(true);
              setForm({ ...form, companySlug: slugify(e.target.value) });
            }}
            required
          />
          <p className="-mt-2 text-xs text-ink-400">
            This is also what your candidates see: /careers/{form.companySlug || "your-company"}
          </p>
          <div className="grid grid-cols-2 gap-4">
            <Input
              id="firstName"
              label="First name"
              value={form.firstName}
              onChange={(e) => setForm({ ...form, firstName: e.target.value })}
              required
            />
            <Input
              id="lastName"
              label="Last name"
              value={form.lastName}
              onChange={(e) => setForm({ ...form, lastName: e.target.value })}
              required
            />
          </div>
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
          {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <Button type="submit" disabled={submitting} className="mt-2 w-full">
            {submitting ? "Creating…" : "Create organization"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-signal-600 hover:text-signal-700">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
