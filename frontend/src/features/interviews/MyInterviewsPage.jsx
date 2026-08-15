import { useState } from "react";
import { useMyInterviews, useSubmitFeedback } from "./useInterviews";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

function FeedbackForm({ interviewId, onDone }) {
  const submitFeedback = useSubmitFeedback();
  const [criterion, setCriterion] = useState("");
  const [score, setScore] = useState("");
  const [rubricScores, setRubricScores] = useState([]);
  const [overallRating, setOverallRating] = useState("");
  const [recommendation, setRecommendation] = useState("yes");
  const [notes, setNotes] = useState("");

  function addRubricRow() {
    if (!criterion || !score) return;
    setRubricScores([...rubricScores, { criterion, score: Number(score) }]);
    setCriterion("");
    setScore("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    await submitFeedback.mutateAsync({
      interviewId,
      rubricScores,
      overallRating: overallRating ? Number(overallRating) : undefined,
      recommendation,
      notes,
    });
    onDone();
  }

  return (
    <form onSubmit={handleSubmit} className="mt-3 flex flex-col gap-3 border-t border-ink-100 pt-3">
      <div className="flex items-end gap-2">
        <Input
          id="criterion"
          label="Criterion"
          value={criterion}
          onChange={(e) => setCriterion(e.target.value)}
          className="w-40"
        />
        <Input
          id="score"
          label="Score (1-5)"
          type="number"
          step="0.5"
          min="1"
          max="5"
          value={score}
          onChange={(e) => setScore(e.target.value)}
          className="w-24"
        />
        <Button type="button" variant="secondary" onClick={addRubricRow}>
          Add
        </Button>
      </div>
      {rubricScores.length > 0 && (
        <ul className="text-xs text-ink-500">
          {rubricScores.map((r, i) => (
            <li key={i}>
              {r.criterion}: {r.score}
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-3">
        <Input
          id="overallRating"
          label="Overall rating (1-5)"
          type="number"
          step="0.5"
          min="1"
          max="5"
          value={overallRating}
          onChange={(e) => setOverallRating(e.target.value)}
          className="w-32"
        />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-ink-700">Recommendation</label>
          <select
            value={recommendation}
            onChange={(e) => setRecommendation(e.target.value)}
            className="rounded-md border border-ink-200 px-3 py-2 text-sm"
          >
            <option value="strong_yes">Strong yes</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="strong_no">Strong no</option>
          </select>
        </div>
      </div>
      <Input id="notes" label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" disabled={submitFeedback.isPending}>
          {submitFeedback.isPending ? "Submitting…" : "Submit feedback"}
        </Button>
      </div>
    </form>
  );
}

export function MyInterviewsPage() {
  const { data: interviews, isLoading } = useMyInterviews();
  const [activeFeedbackId, setActiveFeedbackId] = useState(null);

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-2xl text-ink-900">My interviews</h1>
      <p className="mt-1 text-sm text-ink-500">Rounds you're on the panel for.</p>

      <div className="mt-6 flex flex-col gap-3">
        {isLoading && <p className="text-sm text-ink-400">Loading…</p>}
        {interviews?.length === 0 && (
          <Card className="p-8 text-center text-sm text-ink-500">No interviews assigned to you yet.</Card>
        )}
        {interviews?.map((interview) => (
          <Card key={interview.id} className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-ink-800">{interview.round_name}</p>
                <p className="text-xs capitalize text-ink-500">{interview.status}</p>
              </div>
              {activeFeedbackId !== interview.id && (
                <Button variant="secondary" onClick={() => setActiveFeedbackId(interview.id)}>
                  Submit feedback
                </Button>
              )}
            </div>
            {activeFeedbackId === interview.id && (
              <FeedbackForm interviewId={interview.id} onDone={() => setActiveFeedbackId(null)} />
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
