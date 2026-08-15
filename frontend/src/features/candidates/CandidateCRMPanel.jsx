import { useState } from "react";
import {
  useCandidateNotes,
  useAddCandidateNote,
  useCandidateTags,
  useAddCandidateTag,
} from "./useCandidateCRM";
import { Button } from "../../components/ui/Button";

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
    <div className="grid grid-cols-2 gap-6 bg-ink-50 p-4">
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
  );
}
