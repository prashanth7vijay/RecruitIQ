import { useRef } from "react";
import { useUploadResume } from "./useCandidates";

export function ResumeUploadButton({ profileId }) {
  const inputRef = useRef(null);
  const uploadResume = useUploadResume();

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadResume.mutate(
      { profileId, file },
      {
        onError: () => {
        
        },
      }
    );
    e.target.value = ""; // allow re-selecting the same file name later
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={uploadResume.isPending}
        className="text-xs font-medium text-signal-600 hover:text-signal-700 disabled:opacity-50"
      >
        {uploadResume.isPending ? "Uploading…" : "Upload resume"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.doc"
        className="hidden"
        onChange={handleFileChange}
      />
      {uploadResume.isError && (
        <p className="text-xs text-red-600">
          {uploadResume.error.response?.data?.error?.message ?? "Upload failed."}
        </p>
      )}
      {uploadResume.isSuccess && <p className="text-xs text-signal-600">Uploaded ✓</p>}
    </div>
  );
}
