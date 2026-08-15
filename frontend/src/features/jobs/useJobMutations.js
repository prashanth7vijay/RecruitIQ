import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function usePipelineTemplates() {
  return useQuery({
    queryKey: ["pipeline-templates"],
    queryFn: async () => (await apiClient.get("/pipeline-templates")).data.data,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => (await apiClient.post("/jobs", payload)).data.data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["jobs-paginated"] });
    },
  });
}

export function useSubmitForApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ jobId }) => (await apiClient.post(`/jobs/${jobId}/submit`)).data.data,
    onSuccess: (_data, { jobId }) => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });
}
