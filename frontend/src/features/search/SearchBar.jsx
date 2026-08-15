import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiClient } from "../../lib/apiClient";

function useSearch(query) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: async () => (await apiClient.get(`/search?q=${encodeURIComponent(query)}`)).data.data,
    enabled: query.length >= 2,
  });
}

export function SearchBar() {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const { data } = useSearch(query);

  const hasResults = data && (data.candidates.length > 0 || data.jobs.length > 0);

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Search candidates and jobs…"
        className="w-64 rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-1.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-signal-400 focus:outline-none focus:ring-1 focus:ring-signal-400"
      />
      {open && query.length >= 2 && (
        <div className="absolute left-0 z-10 mt-1 w-72 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] shadow-panel">
          {!hasResults && <p className="p-3 text-xs text-[var(--text-muted)]">No results.</p>}
          {data?.candidates.map((c) => (
            <div key={c.id} className="border-b border-[var(--border)] px-3 py-2 text-xs last:border-0">
              <span className="font-medium text-[var(--text-primary)]">
                {c.candidate?.first_name} {c.candidate?.last_name}
              </span>
              <span className="ml-1 text-[var(--text-muted)]">— candidate</span>
            </div>
          ))}
          {data?.jobs.map((j) => (
            <Link
              key={j.id}
              to={`/jobs/${j.id}`}
              className="block border-b border-[var(--border)] px-3 py-2 text-xs last:border-0 hover:bg-[var(--surface-hover)]"
            >
              <span className="font-medium text-[var(--text-primary)]">{j.title}</span>
              <span className="ml-1 text-[var(--text-muted)]">— job</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
