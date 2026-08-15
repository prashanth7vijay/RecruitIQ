import { useState } from "react";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { useAddCandidate } from "./useCandidates";

export function AddCandidateForm({ onDone }) {
  const [form, setForm] = useState({ email: "", first_name: "", last_name: "", phone: "" });
  const [error, setError] = useState(null);
  const addCandidate = useAddCandidate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      await addCandidate.mutateAsync(form);
      onDone();
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not add candidate.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <Input
          id="first_name"
          label="First name"
          value={form.first_name}
          onChange={(e) => setForm({ ...form, first_name: e.target.value })}
          required
        />
        <Input
          id="last_name"
          label="Last name"
          value={form.last_name}
          onChange={(e) => setForm({ ...form, last_name: e.target.value })}
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
        id="phone"
        label="Phone (optional)"
        value={form.phone}
        onChange={(e) => setForm({ ...form, phone: e.target.value })}
      />
      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={addCandidate.isPending}>
          {addCandidate.isPending ? "Adding…" : "Add candidate"}
        </Button>
      </div>
    </form>
  );
}
