import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useMyInterviews() {
  return useQuery({
    queryKey: ["my-interviews"],
    queryFn: async () => (await apiClient.get("/interviews/mine")).data.data,
  });
}

export function useScheduleInterview(applicationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ roundName, panelistUserIds, scheduledAt }) => {
      const res = await apiClient.post("/interviews", {
        application_id: applicationId,
        round_name: roundName,
        panelist_user_ids: panelistUserIds,
        scheduled_at: scheduledAt || undefined,
      });
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ interviewId, rubricScores, overallRating, recommendation, notes }) => {
      const res = await apiClient.post(`/interviews/${interviewId}/feedback`, {
        rubric_scores: rubricScores,
        overall_rating: overallRating || undefined,
        recommendation: recommendation || undefined,
        notes: notes || undefined,
      });
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-interviews"] });
    },
  });
}
