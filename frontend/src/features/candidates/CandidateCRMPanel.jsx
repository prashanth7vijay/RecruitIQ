import { useState } from "react";
import {
  useCandidateNotes,
  useAddCandidateNote,
  useCandidateTags,
  useAddCandidateTag,
} from "./useCandidateCRM";
import { useTalentPools, useAddToPool } from "../talent-pools/useTalentPools";
import { Button } from "../../components/ui/Button";

function AddToPoolControl({ profileId }) {
  const { data: pools } = useTalentPools();
  const [selectedPoolId, setSelectedPoolId] = useState("");
  const addToPool = useAddToPool(selectedPoolId);
  const [confirmation, setConfirmation] = useState(null);

  async function handleAdd() {
    if (!selectedPoolId) return;
    try {
      await addToPool.mutateAsync(profileId);
      setConfirmation("Added.");
    } catch (err) {
      setConfirmation(err.response?.data?.error?.message ?? "Could not add to pool.");
    }
  }

  if (!pools || pools.length === 0) {
    return <p className="text-xs text-ink-400">No talent pools yet — create one on the Talent Pools page.</p>;
  }

  return (
    <div className="flex items-center gap-1.5">
      <select
        value={selectedPoolId}
        onChange={(e) => {
          setSelectedPoolId(e.target.value);
          setConfirmation(null);
        }}
        className="rounded-md border border-ink-200 px-2 py-1 text-xs"
      >
        <option value="">Add to pool…</option>
        {pools.map((pool) => (
          <option key={pool.id} value={pool.id}>
            {pool.name}
          </option>
        ))}
      </select>
      <Button
        type="button"
        variant="secondary"
        className="px-2 py-1 text-xs"
        disabled={!selectedPoolId || addToPool.isPending}
        onClick={handleAdd}
      >
        Add
      </Button>
      {confirmation && <span className="text-xs text-ink-500">{confirmation}</span>}
    </div>
  );
}

export function CandidateCRMPanel({ profileId }) {
  const { data: notes } = useCandidateNotes(profileId);
  const addNote = useAddCandidateNote(profileId);
  const { data: tags } = useCandidateTags(profileId);
  const addTag = useAddCandidateTag(profileId);
  const [noteText, setNoteText] = useState("");
  const [tagText, setTagText] = useState("");

  async function handleAddNote(e) {
    e.preventDefault();
    if (!noteText.trim()) return;
    await addNote.mutateAsync(noteText);
    setNoteText("");
  }

  async function handleAddTag(e) {
    e.preventDefault();
    if (!tagText.trim()) return;
    await addTag.mutateAsync(tagText);
    setTagText("");
  }

  return (
    <div className="bg-ink-50 p-4">
      <div className="mb-4 border-b border-ink-100 pb-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-500">Talent pools</p>
        <div className="mt-2">
          <AddToPoolControl profileId={profileId} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-500">Tags</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          {tags?.map((tag) => (
            <span key={tag.id} className="rounded-full bg-ink-200 px-2 py-0.5 text-xs text-ink-700">
              {tag.label}
            </span>
          ))}
        </div>
        <form onSubmit={handleAddTag} className="mt-2 flex gap-1.5">
          <input
            value={tagText}
            onChange={(e) => setTagText(e.target.value)}
            placeholder="Add tag…"
            className="w-32 rounded-md border border-ink-200 px-2 py-1 text-xs"
          />
          <Button type="submit" variant="secondary" className="px-2 py-1 text-xs" disabled={addTag.isPending}>
            Add
          </Button>
        </form>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-500">Notes</p>
        <div className="mt-2 flex flex-col gap-1.5">
          {notes?.map((note) => (
            <p key={note.id} className="rounded-md bg-white px-2 py-1.5 text-xs text-ink-700">
              {note.body}
            </p>
          ))}
        </div>
        <form onSubmit={handleAddNote} className="mt-2 flex gap-1.5">
          <input
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Add a note…"
            className="flex-1 rounded-md border border-ink-200 px-2 py-1 text-xs"
          />
          <Button type="submit" variant="secondary" className="px-2 py-1 text-xs" disabled={addNote.isPending}>
            Add
          </Button>
        </form>
      </div>
      </div>
    </div>
  );
}