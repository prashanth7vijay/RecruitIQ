import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useImproveDescription() {
  return useMutation({
    mutationFn: async (jobId) => {
      const res = await apiClient.post(`/ai/jobs/${jobId}/improve-description`);
      return res.data.data; // { suggestion, ai_request_id, status: 'suggested' }
    },
  });
}

export function useApplyDescription(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ aiRequestId, newDescription }) => {
      const res = await apiClient.post(`/ai/jobs/${jobId}/apply-description`, {
        ai_request_id: aiRequestId,
        new_description: newDescription,
      });
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
    },
  });
}

export function useComputeMatchScore(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (applicationId) => {
      const res = await apiClient.post(`/ai/applications/${applicationId}/match-score`);
      return res.data.data; // { score, explanation, ai_request_id, status: 'suggested' }
    },
    onSuccess: () => {
      if (jobId) queryClient.invalidateQueries({ queryKey: ["applications", jobId] });
    },
  });
}

export function useRankCandidates(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (force = false) => {
      const query = force ? "?force=true" : "";
      const res = await apiClient.post(`/ai/jobs/${jobId}/rank-candidates${query}`);
      return res.data.data; // Application[] sorted by match_score descending
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", jobId] });
    },
  });
}
