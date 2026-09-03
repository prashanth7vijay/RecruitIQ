import { useResumeDownloadUrl } from "./useCandidates";

export function ResumeLink({ profileId }) {
  const { refetch, isFetching } = useResumeDownloadUrl(profileId);

  async function handleClick() {
    const { data } = await refetch();
    if (data?.url) {
      window.open(data.url, "_blank", "noopener,noreferrer");
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isFetching}
      className="text-xs font-medium text-signal-600 hover:underline disabled:text-ink-400"
    >
      {isFetching ? "Opening…" : "View resume"}
    </button>
  );
}