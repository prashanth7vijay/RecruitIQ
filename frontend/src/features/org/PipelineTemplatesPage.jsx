import { useState } from "react";
import { useAuth } from "../../stores/AuthContext";
import {
  usePipelineTemplates,
  useCreatePipelineTemplate,
  useUpdatePipelineTemplate,
  useDeletePipelineTemplate,
} from "./usePipelineTemplates";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";

const STAGE_TYPES = ["screening", "interview", "assessment", "offer", "terminal"];

function StageBuilder({ stages, setStages }) {
  const [name, setName] = useState("");
  const [stageType, setStageType] = useState("screening");

  function addStage() {
    if (!name) return;
    setStages([...stages, { name, stage_order: stages.length, stage_type: stageType }]);
    setName("");
  }

  function removeStage(index) {
    setStages(stages.filter((_, i) => i !== index).map((s, i) => ({ ...s, stage_order: i })));
  }

  return (
    <div>
      <div className="flex items-end gap-2">
        <Input id="stage-name" label="Stage name" value={name} onChange={(e) => setName(e.target.value)} />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-[var(--text-primary)]">Type</label>
          <select
            value={stageType}
            onChange={(e) => setStageType(e.target.value)}
            className="rounded-md border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm capitalize text-[var(--text-primary)]"
          >
            {STAGE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <Button type="button" variant="secondary" onClick={addStage} disabled={!name}>
          Add stage
        </Button>
      </div>

      {stages.length > 0 && (
        <ol className="mt-4 flex flex-col gap-2">
          {stages.map((stage, i) => (
            <li
              key={i}
              className="flex items-center justify-between rounded-md bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]"
            >
              <span>
                {i + 1}. {stage.name}{" "}
                <span className="capitalize text-[var(--text-muted)]">({stage.stage_type})</span>
              </span>
              <button type="button" onClick={() => removeStage(i)} className="text-xs text-red-500 hover:text-red-600">
                Remove
              </button>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function CreateTemplateForm({ onDone }) {
  const createTemplate = useCreatePipelineTemplate();
  const [templateName, setTemplateName] = useState("");
  const [stages, setStages] = useState([]);
  const [isDefault, setIsDefault] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (stages.length === 0) {
      setError("Add at least one stage before creating the template.");
      return;
    }
    try {
      await createTemplate.mutateAsync({ name: templateName, stages, isDefault });
      setTemplateName("");
      setStages([]);
      setIsDefault(false);
      onDone();
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not create pipeline template.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <Input
        id="template-name"
        label="Template name"
        value={templateName}
        onChange={(e) => setTemplateName(e.target.value)}
        required
      />
      <StageBuilder stages={stages} setStages={setStages} />
      <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
        <input
          type="checkbox"
          checked={isDefault}
          onChange={(e) => setIsDefault(e.target.checked)}
          className="accent-signal-500"
        />
        Make this the default pipeline for new jobs
      </label>
      {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
      <Button type="submit" disabled={createTemplate.isPending || !templateName} className="self-start">
        {createTemplate.isPending ? "Creating…" : "Create template"}
      </Button>
    </form>
  );
}

function TemplateCard({ template, canManage }) {
  const [editing, setEditing] = useState(false);
  const [stages, setStages] = useState(
    template.stages.map(({ name, stage_order, stage_type }) => ({ name, stage_order, stage_type }))
  );
  const updateTemplate = useUpdatePipelineTemplate();
  const deleteTemplate = useDeletePipelineTemplate();
  const [error, setError] = useState(null);

  async function handleSaveStages() {
    setError(null);
    try {
      await updateTemplate.mutateAsync({ templateId: template.id, stages });
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not save changes.");
    }
  }

  async function handleToggleDefault() {
    setError(null);
    try {
      await updateTemplate.mutateAsync({ templateId: template.id, isDefault: !template.is_default });
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not update default pipeline.");
    }
  }

  async function handleDelete() {
    setError(null);
    try {
      await deleteTemplate.mutateAsync(template.id);
    } catch (err) {
      setError(err.response?.data?.error?.message ?? "Could not delete — it may still be used by a job.");
    }
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium text-[var(--text-primary)]">
            {template.name}
            {template.is_default && (
              <span className="ml-2 rounded-full bg-signal-100 px-2 py-0.5 text-[10px] uppercase text-signal-700 dark:bg-signal-900 dark:text-signal-300">
                Default
              </span>
            )}
          </p>
          {!editing && (
            <p className="mt-1 text-xs text-[var(--text-secondary)]">
              {template.stages.map((s) => s.name).join(" \u2192 ")}
            </p>
          )}
        </div>
        {canManage && (
          <div className="flex gap-2">
            <Button variant="ghost" className="!px-2 !py-1 text-xs" onClick={handleToggleDefault}>
              {template.is_default ? "Unset default" : "Set default"}
            </Button>
            <Button variant="ghost" className="!px-2 !py-1 text-xs" onClick={() => setEditing((e) => !e)}>
              {editing ? "Cancel" : "Edit stages"}
            </Button>
            <Button variant="ghost" className="!px-2 !py-1 text-xs text-red-600" onClick={handleDelete}>
              Delete
            </Button>
          </div>
        )}
      </div>

      {editing && (
        <div className="mt-3">
          <StageBuilder stages={stages} setStages={setStages} />
          <Button className="mt-3" onClick={handleSaveStages} disabled={updateTemplate.isPending || stages.length === 0}>
            {updateTemplate.isPending ? "Saving…" : "Save stages"}
          </Button>
        </div>
      )}
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </Card>
  );
}

export function PipelineTemplatesPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("pipeline.manage");
  const { data: templates, isLoading } = usePipelineTemplates();
  const [showCreate, setShowCreate] = useState(false);

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl text-[var(--text-primary)]">Pipeline templates</h1>
      <p className="mt-1 text-sm text-[var(--text-secondary)]">
        Reusable hiring stages you can assign to any job. Every job needs one of these before it
        can be published.
      </p>
      {!canManage && (
        <p className="mt-4 rounded-md border border-[var(--border)] bg-[var(--surface-hover)] px-3 py-2 text-sm text-[var(--text-secondary)]">
          Only organization admins design pipelines — you can view and use existing templates when
          creating a job.
        </p>
      )}

      {canManage && (
        <Card className="mt-6 p-6">
          {!showCreate ? (
            <Button onClick={() => setShowCreate(true)}>+ New pipeline template</Button>
          ) : (
            <>
              <p className="mb-4 font-display text-lg text-[var(--text-primary)]">New template</p>
              <CreateTemplateForm onDone={() => setShowCreate(false)} />
              <Button variant="ghost" className="mt-3" onClick={() => setShowCreate(false)}>
                Cancel
              </Button>
            </>
          )}
        </Card>
      )}

      <div className="mt-8">
        <h2 className="font-display text-lg text-[var(--text-primary)]">Existing templates</h2>
        {isLoading && <p className="mt-2 text-sm text-[var(--text-muted)]">Loading…</p>}
        <div className="mt-3 flex flex-col gap-2">
          {templates?.map((t) => (
            <TemplateCard key={t.id} template={t} canManage={canManage} />
          ))}
        </div>
      </div>
    </div>
  );
}
