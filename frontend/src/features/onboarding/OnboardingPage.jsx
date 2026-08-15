import { useParams, Link } from "react-router-dom";
import { useOnboardingByApplication, useCompleteTask } from "./useOnboarding";
import { Card } from "../../components/ui/Card";

export function OnboardingPage() {
  const { applicationId } = useParams();
  const { data: checklist, isLoading, isError } = useOnboardingByApplication(applicationId);
  const completeTask = useCompleteTask(applicationId);

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/jobs" className="text-sm text-ink-500 hover:text-ink-700">
        ← Back to jobs
      </Link>
      <h1 className="mt-4 font-display text-2xl text-ink-900">Onboarding</h1>

      {isLoading && <p className="mt-4 text-sm text-ink-400">Loading…</p>}
      {isError && (
        <p className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-700">
          No onboarding checklist found yet for this candidate.
        </p>
      )}

      {checklist && (
        <Card className="mt-6 p-6">
          <p className="text-sm capitalize text-ink-500">Status: {checklist.status.replace("_", " ")}</p>
          <ul className="mt-4 flex flex-col gap-2">
            {checklist.tasks.map((task) => (
              <li key={task.id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={task.is_completed}
                  disabled={task.is_completed || completeTask.isPending}
                  onChange={() => completeTask.mutate(task.id)}
                  className="h-4 w-4 rounded border-ink-300 text-signal-500"
                />
                <span className={task.is_completed ? "text-ink-400 line-through" : "text-ink-700"}>
                  {task.title}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
