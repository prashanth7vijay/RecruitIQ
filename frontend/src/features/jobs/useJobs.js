import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/apiClient";

export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: async () => (await apiClient.get("/jobs")).data.data,
  });
}

export function useJobsPaginated(page = 1) {
  return useQuery({
    queryKey: ["jobs-paginated", page],
    queryFn: async () => {
      const res = await apiClient.get(`/jobs?page=${page}`);
      return { items: res.data.data, pagination: res.data.meta.pagination };
    },
  });
}

export function useJob(jobId) {
  return useQuery({
    queryKey: ["job", jobId],
    queryFn: async () => (await apiClient.get(`/jobs/${jobId}`)).data.data,
    enabled: Boolean(jobId),
  });
}

export function usePipelineTemplate(templateId) {
  return useQuery({
    queryKey: ["pipeline-template", templateId],
    queryFn: async () => (await apiClient.get(`/pipeline-templates/${templateId}`)).data.data,
    enabled: Boolean(templateId),
  });
}

export function useApplicationsForJob(jobId) {
  return useQuery({
    queryKey: ["applications", jobId],
    queryFn: async () => (await apiClient.get(`/applications?job_id=${jobId}`)).data.data,
    enabled: Boolean(jobId),
  });
}

export function useApprovalSteps(jobId, enabled) {
  return useQuery({
    queryKey: ["approval-steps", jobId],
    queryFn: async () => (await apiClient.get(`/jobs/${jobId}/approval-steps`)).data.data,
    enabled: Boolean(jobId) && enabled,
  });
}

export function useApproveStep(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (stepId) =>
      (await apiClient.post(`/jobs/${jobId}/approval-steps/${stepId}/approve`, {})).data.data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      queryClient.invalidateQueries({ queryKey: ["approval-steps", jobId] });
    },
  });
}

export function useCloseJob(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await apiClient.post(`/jobs/${jobId}/close`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });
}

export function useArchiveJob(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await apiClient.post(`/jobs/${jobId}/archive`)).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job", jobId] }),
  });
}

export function useRejectApplication(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ applicationId, reason }) =>
      (await apiClient.post(`/applications/${applicationId}/reject`, { reason })).data.data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications", jobId] }),
  });
}

export function useMoveApplicationStage(jobId) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ applicationId, targetStageId }) => {
      const res = await apiClient.patch(`/applications/${applicationId}/stage`, {
        target_stage_id: targetStageId,
      });
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", jobId] });
    },
  });
}
