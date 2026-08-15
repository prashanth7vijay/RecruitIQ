export function Card({ className = "", children }) {
  return (
    <div
      className={`rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] shadow-soft ${className}`}
    >
      {children}
    </div>
  );
}
