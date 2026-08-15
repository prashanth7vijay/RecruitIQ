import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useOnboardingByApplication(applicationId) {
  return useQuery({
    queryKey: ["onboarding", applicationId],
    queryFn: async () => (await apiClient.get(`/onboarding/by-application/${applicationId}`)).data.data,
    enabled: Boolean(applicationId),
    retry: false, // a 404 here is expected until an offer's been accepted — don't retry-spam it
  });
}

export function useCompleteTask(applicationId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId) => (await apiClient.patch(`/onboarding/tasks/${taskId}/complete`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["onboarding", applicationId] }),
  });
}
