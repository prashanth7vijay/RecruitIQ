import { useState } from "react";
import { useImproveDescription, useApplyDescription } from "./useAI";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";

export function JobDescriptionPanel({ job }) {
  const improveDescription = useImproveDescription();
  const applyDescription = useApplyDescription(job.id);
  const [suggestion, setSuggestion] = useState(null); // { suggestion, ai_request_id }
  const [editedText, setEditedText] = useState("");

  async function handleImprove() {
    const result = await improveDescription.mutateAsync(job.id);
    setSuggestion(result);
    setEditedText(result.suggestion);
  }

  async function handleAccept() {
    await applyDescription.mutateAsync({
      aiRequestId: suggestion.ai_request_id,
      newDescription: editedText,
    });
    setSuggestion(null);
  }

  function handleDiscard() {
   
    setSuggestion(null);
  }

  return (
    <Card className="mt-6 p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg text-ink-900">Description</h2>
        {!suggestion && (
          <button
            onClick={handleImprove}
            disabled={improveDescription.isPending}
            className="text-xs font-medium text-signal-600 hover:text-signal-700 disabled:opacity-50"
          >
            {improveDescription.isPending ? "Asking AI…" : "✨ Improve with AI"}
          </button>
        )}
      </div>

      {improveDescription.isError && (
        <p className="mt-2 rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">
          {improveDescription.error.response?.data?.error?.message ??
            "Couldn't reach the AI provider. Is Ollama running?"}
        </p>
      )}

      {!suggestion && (
        <p className="mt-3 whitespace-pre-line text-sm text-ink-600">
          {job.description || "No description yet."}
        </p>
      )}

      {suggestion && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-signal-600">
            AI suggestion — review before accepting
          </p>
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            rows={8}
            className="mt-2 w-full rounded-md border border-ink-200 p-3 text-sm text-ink-700 focus:border-signal-400 focus:outline-none focus:ring-1 focus:ring-signal-400"
          />
          <div className="mt-2 flex justify-end gap-2">
            <Button variant="ghost" onClick={handleDiscard}>
              Discard
            </Button>
            <Button onClick={handleAccept} disabled={applyDescription.isPending}>
              {applyDescription.isPending ? "Saving…" : "Accept & save"}
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
